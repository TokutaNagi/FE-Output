import uuid

import pytest
from playwright.sync_api import expect, sync_playwright


BASE_URL = "http://127.0.0.1:8000"

TEST_USERNAME = f"testuser_{uuid.uuid4().hex[:8]}"
TEST_PASSWORD = "TestPassword123!"


class TestE2E:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=False,
            slow_mo=200,
        )
        self.page = self.browser.new_page()

        yield

        self.browser.close()
        self.playwright.stop()

    def test_user_flow(self):
        #
        # 新規登録
        #
        self.page.goto(f"{BASE_URL}/signup/")

        self.page.fill("input[name='username']", TEST_USERNAME)
        self.page.fill("input[name='password1']", TEST_PASSWORD)
        self.page.fill("input[name='password2']", TEST_PASSWORD)

        self.page.click("button[type='submit']")

        expect(self.page).to_have_url(f"{BASE_URL}/login/")

        #
        # ログイン
        #
        self.page.fill("input[name='username']", TEST_USERNAME)
        self.page.fill("input[name='password']", TEST_PASSWORD)

        self.page.click("button[type='submit']")

        expect(self.page).to_have_url(f"{BASE_URL}/")

        #
        # ゲーム開始
        #
        self.page.locator("input[name='categories']").first.check()
        self.page.select_option("select[name='count']", "10")

        self.page.click("button:has-text('開始')")

        expect(self.page).to_have_url(f"{BASE_URL}/question/")

        #
        # 1問進める
        #
        first_question = True

        while "result" not in self.page.url:
            if first_question:
                self.page.fill("input[name='answer']", "xxxxxxxx")
                self.page.click("button:has-text('回答')")

                while not self.page.locator("button:has-text('次へ')").count():
                    self.page.click("button:has-text('ヒント')")

                self.page.click("button:has-text('次へ')")
                first_question = False

            else:
                answer = self.page.locator("#correct-answer").input_value()

                self.page.fill("input[name='answer']", answer)
                self.page.click("button:has-text('回答')")

                self.page.wait_for_selector("button:has-text('次へ')")
                self.page.click("button:has-text('次へ')")

        #
        # リザルト画面
        #
        expect(self.page).to_have_url(f"{BASE_URL}/result/")

        expect(self.page.locator("body")).to_contain_text("正答率")

        self.page.wait_for_timeout(5000)

        #
        # マイページへ
        #
        self.page.click("a:has-text('間違えた用語集')")

        expect(self.page).to_have_url(f"{BASE_URL}/mypage/")

        self.page.wait_for_timeout(5000)

        #
        # 苦手問題を解く
        #
        with self.page.expect_navigation():
            self.page.click("a:has-text('苦手問題を解く')")

        self.page.wait_for_load_state("networkidle")
        print(self.page.url)

        expect(self.page).to_have_url(f"{BASE_URL}/question/")

        #
        # 苦手問題を最後まで解く
        #
        while "result" not in self.page.url:
            answer = self.page.locator("#correct-answer").input_value()

            self.page.fill(
                "input[name='answer']",
                answer,
            )

            self.page.click("button:has-text('回答')")

            self.page.wait_for_selector(
                "button:has-text('次へ')",
                timeout=3000,
            )

            self.page.click("button:has-text('次へ')")

        #
        # 苦手問題のリザルト
        #
        expect(self.page).to_have_url(f"{BASE_URL}/result/")
        expect(self.page.locator("body")).to_contain_text("正答率")

        self.page.wait_for_timeout(5000)
