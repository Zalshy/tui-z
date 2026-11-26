from textual.color import Color

from tui_z import Text, TwApp


class FewChunks(TwApp):
    TW_MAX_CHUNKS = 2


async def test_chunks_are_consolidated_and_styles_survive(mount):
    t = Text("x", id="t")
    async with mount(t, app_class=FewChunks) as (app, pilot):
        for i in range(6):  # each new string on a live widget adds a chunk
            t.set_cls(f"text-[#0000{i:02x}]")
            await pilot.pause()
            assert t.styles.color == Color.parse(f"#0000{i:02x}")
        assert app._tw_sheet.chunks <= FewChunks.TW_MAX_CHUNKS
        sources = [k for k in app.stylesheet.source if k[0] == "tui_z"]
        assert len(sources) <= FewChunks.TW_MAX_CHUNKS
