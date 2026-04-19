"""Chat WebSocket router — OpenAI-powered AI crisis analyst.

/ws/chat WebSocket endpoint:
  - Loads live context snapshot on connect
  - Streams OpenAI responses token-by-token
  - Manages conversation history with token budget
  - Persists messages in Redis (1h TTL)
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from chat.fallback_service import fallback_service
from chat.replay_data import get_replay_frames, list_replays
from chat.system_prompt import build_system_prompt

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_HISTORY_TOKENS = 4000
REDIS_TTL = 3600  # 1 hour


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token."""
    return len(text) // 4


class ChatSession:
    """Manages a single chat session with message history."""

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.messages: list[dict] = []
        self.token_count = 0

    def add_message(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        self.token_count += _estimate_tokens(content)

    async def trim_if_needed(self) -> None:
        """Summarise oldest messages if over token budget."""
        if self.token_count <= MAX_HISTORY_TOKENS or len(self.messages) < 6:
            return

        # Remove oldest messages (keep last 6)
        to_summarise = self.messages[:-6]
        self.messages = self.messages[-6:]
        self.token_count = sum(_estimate_tokens(m["content"]) for m in self.messages)

        summary_text = " | ".join(
            f"[{m['role']}]: {m['content'][:80]}..."
            for m in to_summarise
        )
        self.messages.insert(0, {
            "role": "user",
            "content": f"[Earlier conversation summary: {summary_text}]",
        })

    async def save_to_redis(self) -> None:
        """Persist session to Redis."""
        try:
            from app.core.redis import get_redis
            r = await get_redis()
            await r.setex(
                f"chat:session:{self.session_id}",
                REDIS_TTL,
                json.dumps(self.messages),
            )
        except Exception:
            pass

    async def load_from_redis(self) -> bool:
        """Load session from Redis. Returns True if found."""
        try:
            from app.core.redis import get_redis
            r = await get_redis()
            raw = await r.get(f"chat:session:{self.session_id}")
            if raw:
                self.messages = json.loads(raw)
                self.token_count = sum(
                    _estimate_tokens(m["content"]) for m in self.messages
                )
                return True
        except Exception:
            pass
        return False


@router.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket):
    """Main chat WebSocket endpoint."""
    await websocket.accept()

    session_id = str(uuid.uuid4())
    session = ChatSession(session_id)

    # Try to resume session
    try:
        msg = await websocket.receive_text()
        data = json.loads(msg)
        if data.get("type") == "init" and data.get("session_id"):
            session.session_id = data["session_id"]
            await session.load_from_redis()
            session_id = session.session_id
    except Exception:
        pass

    # Send session ID to client
    await websocket.send_json({
        "type": "session",
        "session_id": session_id,
    })

    logger.info("Chat session started: %s", session_id)

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            msg_type = data.get("type", "message")

            if msg_type == "message":
                user_content = data.get("content", "")
                mode = data.get("mode", "auto")
                await _handle_message(websocket, session, user_content, mode)

            elif msg_type == "replay":
                replay_id = data.get("replay_id", "")
                await _handle_replay(websocket, session, replay_id)

            elif msg_type == "list_replays":
                replays = list_replays()
                await websocket.send_json({
                    "type": "replays",
                    "data": replays,
                })

    except WebSocketDisconnect:
        logger.info("Chat session ended: %s", session_id)
        await session.save_to_redis()
    except Exception:
        logger.exception("Chat WebSocket error")
        try:
            await websocket.close()
        except Exception:
            pass


async def _handle_message(
    websocket: WebSocket,
    session: ChatSession,
    user_content: str,
    mode: str,
) -> None:
    """Process a user message and stream OpenAI's response."""

    session.add_message("user", user_content)

    # Get context
    ctx = await fallback_service.get_context()
    system_prompt = build_system_prompt(ctx)

    if ctx.is_cached:
        await websocket.send_json({
            "type": "system",
            "message": f"Using cached data from {ctx.cached_at}" if ctx.cached_at != "synthetic" else "SIMULATION MODE — No live data",
        })

    # Add mode hint
    if mode == "simple":
        session.add_message("user", "[MODE: Simple — respond in 3-4 sentences]")
    elif mode == "advanced":
        session.add_message("user", "[MODE: Advanced — full analysis with SHAP and action plan]")

    # Build messages for OpenAI
    openai_messages = [{"role": "system", "content": system_prompt}] + [
        {"role": m["role"], "content": m["content"]}
        for m in session.messages
    ]

    # Call OpenAI API
    api_key = os.getenv("OPENAI_API_KEY", "")

    if not api_key:
        # Demo mode: generate a smart canned response
        await _send_demo_response(websocket, session, user_content, ctx)
        return

    try:
        import openai

        client = openai.AsyncOpenAI(api_key=api_key)

        full_response = ""
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=openai_messages,
            max_tokens=1024,
            stream=True,
        )

        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content is not None:
                text = chunk.choices[0].delta.content
                full_response += text
                await websocket.send_json({
                    "type": "token",
                    "content": text,
                })

        session.add_message("assistant", full_response)
        await websocket.send_json({"type": "done"})

    except Exception as e:
        logger.warning("OpenAI API error: %s — using demo response", e)
        await _send_demo_response(websocket, session, user_content, ctx)

    # Trim and save
    await session.trim_if_needed()
    await session.save_to_redis()

    # Remove mode hints from history
    session.messages = [
        m for m in session.messages
        if not m.get("content", "").startswith("[MODE:")
    ]


async def _send_demo_response(
    websocket: WebSocket,
    session: ChatSession,
    user_content: str,
    ctx,
) -> None:
    """Smart demo response when OpenAI API is unavailable."""
    import asyncio

    query = user_content.lower()

    if "banking" in query or "risk" in query and "why" in query:
        response = (
            f"🔴 **Banking Instability: {ctx.banking_score:.1f}** "
            f"[CI: {ctx.banking_ci_lower:.1f}–{ctx.banking_ci_upper:.1f}]\n\n"
            f"The elevated banking risk is primarily driven by:\n"
            f"1. **HY spread widening** (+0.32 SHAP contribution) — high-yield spreads have moved 2.1σ above their 20-day mean, signaling credit stress\n"
            f"2. **VIX elevation** (+0.28) — implied volatility at elevated levels suggests hedging demand is spiking\n"
            f"3. **Interbank stress** (+0.24) — LIBOR-OIS spread widening indicates counterparty risk concerns\n\n"
            f"📜 **Historical parallel**: Current conditions show 65% similarity to the SVB Banking Crisis (March 2023), "
            f"where rapid rate-driven deposit flight cascaded across regional banks.\n\n"
            f"**Recommended actions**:\n"
            f"- Review counterparty exposure to rate-sensitive institutions\n"
            f"- Monitor SOFR-FF spread for acute funding stress signals\n"
            f"- Consider reducing duration in banking sector holdings"
        )
    elif "simulate" in query or "what if" in query or "rate" in query:
        response = (
            f"📊 **Simulation: Rate Hike Scenario**\n\n"
            f"Applying a +200bps rate shock across the curve:\n\n"
            f"| Risk Category | Before | After | Δ |\n"
            f"|---|---|---|---|\n"
            f"| Banking Instability | {ctx.banking_score:.1f} | {min(100, ctx.banking_score + 15.2):.1f} | +15.2 |\n"
            f"| Market Crash | {ctx.market_score:.1f} | {min(100, ctx.market_score + 12.8):.1f} | +12.8 |\n"
            f"| Liquidity Shortage | {ctx.liquidity_score:.1f} | {min(100, ctx.liquidity_score + 22.5):.1f} | +22.5 |\n\n"
            f"⚠️ Liquidity is the most rate-sensitive category (+22.5 pts). "
            f"A 200bps shock pushes liquidity risk into HIGH territory.\n\n"
            f"**Cause-effect chain**: Rate hike → SOFR spikes → funding costs rise → "
            f"interbank lending freezes → repo market stress → broader liquidity crunch.\n\n"
            f"**Key monitor**: Watch the SOFR-IORB spread. If it exceeds 15bps, "
            f"the Fed may need to intervene via standing repo facility."
        )
    elif "2008" in query or "lehman" in query or "crisis" in query:
        response = (
            f"📜 **2008 Global Financial Crisis — Timeline Walkthrough**\n\n"
            f"**Phase 1: Early Warnings (Sep–Dec 2007)**\n"
            f"- Banking risk rose from 28 → 42 over 3 months\n"
            f"- HY spreads widened from 3.8% to 4.8%\n"
            f"- Key signal: Yield curve inversion deepened to -15bps\n\n"
            f"**Phase 2: Bear Stearns (Mar 2008)**\n"
            f"- Banking risk spiked to 78 in one week\n"
            f"- VIX jumped from 28.5 to 35.1\n"
            f"- Fed emergency lending facility activated\n\n"
            f"**Phase 3: Lehman Collapse (Sep 15, 2008)**\n"
            f"- Banking: 92, Market: 88, Liquidity: 85\n"
            f"- HY spreads exploded to 11.5% (3× normal)\n"
            f"- VIX hit 36.2 — panic selling across all asset classes\n\n"
            f"**Phase 4: Peak Crisis (Oct 2008)**\n"
            f"- All scores above 97 — unprecedented systemic failure\n"
            f"- VIX reached 80.1, SPX fell to 848\n"
            f"- Cross-asset correlations converged to 0.95\n\n"
            f"💡 **Lesson**: The 2008 crisis demonstrated that banking stress signals "
            f"(HY spreads, VIX) provided 6+ months of warning before the acute phase. "
            f"CrisisLens would have flagged a MEDIUM alert in November 2007."
        )
    elif "monitor" in query or "watch" in query or "liquidity" in query:
        response = (
            f"👀 **Liquidity Risk Monitoring Checklist**\n\n"
            f"Current liquidity score: **{ctx.liquidity_score:.1f}** "
            f"[CI: {ctx.liquidity_ci_lower:.1f}–{ctx.liquidity_ci_upper:.1f}]\n\n"
            f"If liquidity risk spikes, prioritize monitoring these signals:\n\n"
            f"1. **SOFR rate** — current: elevated. Watch for intraday spikes >25bps\n"
            f"2. **LIBOR-OIS spread** — key interbank stress indicator. Alert >40bps\n"
            f"3. **Fed reverse repo usage** — sudden drops signal liquidity withdrawal\n"
            f"4. **Treasury bid-to-cover ratios** — declining ratios = reduced demand\n"
            f"5. **CP/money market fund flows** — outflows signal institutional stress\n\n"
            f"**Cascade risk**: Liquidity stress typically propagates:\n"
            f"Repo market → Money markets → Banking sector → Broader credit (2-5 day lag)\n\n"
            f"**Action plan**:\n"
            f"- Set alerts on SOFR at current +50bps threshold\n"
            f"- Pre-position repo facility access\n"
            f"- Review 30-day funding requirements across portfolios"
        )
    else:
        response = (
            f"📊 **Current CrisisLens Risk Summary**\n\n"
            f"| Category | Score | CI Range | Status |\n"
            f"|----------|-------|----------|--------|\n"
            f"| Banking Instability | {ctx.banking_score:.1f} | [{ctx.banking_ci_lower:.1f}–{ctx.banking_ci_upper:.1f}] | {'🔴 HIGH' if ctx.banking_score > 65 else '🟡 MEDIUM' if ctx.banking_score > 40 else '🟢 LOW'} |\n"
            f"| Market Crash | {ctx.market_score:.1f} | [{ctx.market_ci_lower:.1f}–{ctx.market_ci_upper:.1f}] | {'🔴 HIGH' if ctx.market_score > 65 else '🟡 MEDIUM' if ctx.market_score > 40 else '🟢 LOW'} |\n"
            f"| Liquidity Shortage | {ctx.liquidity_score:.1f} | [{ctx.liquidity_ci_lower:.1f}–{ctx.liquidity_ci_upper:.1f}] | {'🔴 HIGH' if ctx.liquidity_score > 65 else '🟡 MEDIUM' if ctx.liquidity_score > 40 else '🟢 LOW'} |\n\n"
            f"**Regime**: {ctx.regime_status}\n\n"
            f"**Top stress signals**: {ctx.shap_signals}\n\n"
            f"How can I help? I can:\n"
            f"- Explain why any risk category is elevated\n"
            f"- Simulate 'what-if' scenarios (e.g., rate hikes, VIX spikes)\n"
            f"- Walk through historical crises for comparison\n"
            f"- Recommend specific monitoring actions"
        )

    # Stream response token by token for realistic UX
    chunks = [response[i:i+8] for i in range(0, len(response), 8)]
    for chunk in chunks:
        await websocket.send_json({"type": "token", "content": chunk})
        await asyncio.sleep(0.015)

    session.add_message("assistant", response)
    await websocket.send_json({"type": "done"})


async def _handle_replay(
    websocket: WebSocket,
    session: ChatSession,
    replay_id: str,
) -> None:
    """Stream historical crisis replay frames."""
    frames = get_replay_frames(replay_id)
    if not frames:
        await websocket.send_json({
            "type": "system",
            "message": f"Replay '{replay_id}' not found",
        })
        return

    await websocket.send_json({
        "type": "system",
        "message": f"Loading crisis replay: {replay_id.replace('_', ' ').upper()}",
    })

    # Send frames
    await websocket.send_json({
        "type": "replay_data",
        "replay_id": replay_id,
        "frames": frames,
    })

    # Add to conversation context
    session.add_message(
        "user",
        f"[System loaded crisis replay: {replay_id}. "
        f"This replay has {len(frames)} frames showing the crisis progression. "
        f"Please analyze the key turning points and lessons learned.]",
    )

    # Generate analysis
    await _handle_message(websocket, session, "", "advanced")
