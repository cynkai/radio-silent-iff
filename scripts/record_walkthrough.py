import argparse
import time
from pathlib import Path

from playwright.sync_api import Locator, Page, sync_playwright


def hold(page: Page, seconds: float) -> None:
    page.wait_for_timeout(max(0, seconds) * 1000)


def focus_section(page: Page, element: Locator) -> None:
    element.wait_for()
    hold(page, .7)
    element.evaluate("(element) => element.scrollIntoView({block: 'start'})")
    hold(page, .3)
    element.evaluate("(element) => element.scrollIntoView({block: 'start'})")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8502/")
    parser.add_argument("--output", type=Path, default=Path("docs/media/walkthrough.webm"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    captures = Path("docs/img")
    captures.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(viewport={"width": 1440, "height": 900},
                                      record_video_dir=str(args.output.parent),
                                      record_video_size={"width": 1440, "height": 900},
                                      color_scheme="dark", reduced_motion="no-preference")
        page = context.new_page()
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
        started = time.monotonic()
        page.goto(args.url)
        scene = page.locator(".st-key-motion_protocol iframe").content_frame
        scene.locator('[data-component="protocol"]').wait_for()
        scene.get_by_role("button", name="프로토콜 다시 재생").click()
        for stage, progress in (("start", .03), ("middle", .5), ("end", 1)):
            scene.locator("#visual").evaluate("""(element, progress) => new Promise(resolve => {
                const timer = setInterval(() => {
                    if (Number(element.dataset.progress) >= progress) {
                        clearInterval(timer); resolve();
                    }
                }, 30);
            })""", progress)
            page.screenshot(path=str(captures / f"visual-e-desktop-{stage}.png"))
        hold(page, 3)
        print("Signature scene recorded", flush=True)

        page.get_by_role("button", name="① 3분 가이드 투어").click()
        page.get_by_role("button", name="투어 종료", exact=True).wait_for()
        for index in range(9):
            page.get_by_text(f"3분 가이드 투어 · {index + 1}/9", exact=True).wait_for()
            focus_section(page, page.locator(".st-key-tour_scene"))
            hold(page, 4)
            if index < 8:
                page.get_by_role("button", name="다음", exact=True).click()
        page.get_by_role("button", name="투어 종료", exact=True).click()
        print("Nine guide scenes recorded", flush=True)

        page.get_by_role("button", name="② 공격 실험에서 직접 공격").click()
        for preset in ("중계 25µs — 통과(알려진 한계)", "중계 40µs — RTT 차단"):
            page.get_by_role("button", name=preset, exact=True).click()
            host = page.get_by_role("tabpanel", name="레드팀 샌드박스", exact=True).locator("iframe")
            host.content_frame.locator('[data-component="pipeline"]').wait_for()
            host.evaluate("(element) => element.scrollIntoView({block: 'center'})")
            host.content_frame.get_by_role("button", name="파이프라인 다시 재생").click()
            hold(page, 9)
        print("Relay presets recorded", flush=True)

        page.get_by_text("기존 시나리오", exact=True).click()
        briefing = page.locator(".st-key-situation_briefing")
        briefing.locator(".console-badge").wait_for()
        focus_section(page, briefing)
        hold(page, 12)
        page.screenshot(path=str(captures / "visual-e-briefing.png"))
        query = page.locator(".st-key-operator_query")
        query.get_by_role("button", name="예시 답변 보기").click()
        focus_section(page, query)
        hold(page, 8)
        print("Evidence verification recorded using labeled offline examples", flush=True)

        page.get_by_role("button", name="③ 한계 분석 확인").click()
        limits = page.get_by_role("tabpanel", name="④ 한계 분석", exact=True)
        focus_section(page, limits)
        hold(page, 8)
        page.screenshot(path=str(captures / "visual-e-limits.png"))
        last_chart = limits.locator("[data-testid=stPlotlyChart]").last
        focus_section(page, last_chart)
        hold(page, 120 - (time.monotonic() - started))
        if errors:
            raise RuntimeError(f"Browser errors: {errors}")
        video = page.video
        context.close()
        video.save_as(str(args.output))
        video.delete()
        browser.close()
        print(f"Saved {args.output}; elapsed {time.monotonic() - started:.1f}s; browser errors: 0", flush=True)


if __name__ == "__main__":
    main()
