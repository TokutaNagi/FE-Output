from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from terms.models import (
    Category,
    Result,
    ResultDetail,
    Term,
    UserTermStat,
)


class TopViewTest(TestCase):
    # 準備
    def setUp(self):
        Category.objects.create(name="ネットワーク")
        Category.objects.create(name="データベース")

    # カテゴリ表示
    def test_top_page(self):
        response = self.client.get(reverse("top"))

        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "ネットワーク")
        self.assertContains(response, "データベース")


class SignupViewTest(TestCase):
    # GET処理
    def test_signup_get(self):
        response = self.client.get(reverse("signup"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "terms/signup.html")

    # POST処理
    def test_signup_success(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "nagi",
                "password1": "TestPassword123!",
                "password2": "TestPassword123!",
            },
        )

        self.assertRedirects(response, reverse("login"))
        self.assertEqual(User.objects.count(), 1)
        self.assertTrue(User.objects.filter(username="nagi").exists())

    # 確認パスワードエラー
    def test_signup_password_mismatch(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "nagi",
                "password1": "TestPassword123!",
                "password2": "ngpassword",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 0)


class LoginViewTest(TestCase):
    # 画面表示
    def test_login_get(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "terms/login.html")

    # 正常処理
    def test_login_success(self):
        User.objects.create_user(
            username="nagi",
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse("login"),
            {
                "username": "nagi",
                "password": "TestPassword123!",
            },
        )

        self.assertRedirects(response, reverse("top"))

    # パスワードエラー
    def test_login_wrong_password(self):
        User.objects.create_user(
            username="nagi",
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse("login"),
            {
                "username": "nagi",
                "password": "wrongpassword",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "ユーザー名またはパスワードが違います。",
        )

    # 未入力
    def test_login_empty(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": "",
                "password": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "ユーザー名とパスワードを入力してください。",
        )


class StartViewTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="ネットワーク",
        )

        self.term = Term.objects.create(
            category=self.category,
            word="TCP",
            description="説明",
        )

    # カテゴリ未選択
    def test_start_no_category(self):
        response = self.client.get(
            reverse("start"),
            {
                "count": 10,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "terms/top.html")
        self.assertContains(
            response,
            "カテゴリを1つ以上選択してください。",
        )

    # 問題数が不正
    def test_start_invalid_count(self):
        response = self.client.get(
            reverse("start"),
            {
                "categories": [self.category.id],
                "count": 99,
            },
        )

        self.assertRedirects(
            response,
            reverse("game_error"),
        )

    # 正常開始
    def test_start(self):
        response = self.client.get(
            reverse("start"),
            {
                "categories": [self.category.id],
                "count": 10,
            },
        )

        self.assertRedirects(
            response,
            reverse("question"),
        )

    # セッション初期化
    def test_start_session(self):
        self.client.get(
            reverse("start"),
            {
                "categories": [self.category.id],
                "count": 10,
            },
        )

        session = self.client.session

        self.assertEqual(
            session["answers"],
            [],
        )

        self.assertEqual(
            session["current_question"],
            {
                "hint_count": 0,
                "mistaken": False,
            },
        )

        self.assertEqual(
            session["current_index"],
            0,
        )

    # question_ids保存
    def test_start_question_ids(self):
        self.client.get(
            reverse("start"),
            {
                "categories": [self.category.id],
                "count": 10,
            },
        )

        session = self.client.session

        self.assertEqual(
            session["question_ids"],
            [self.term.id],
        )

    # game保存
    def test_start_game_session(self):
        self.client.get(
            reverse("start"),
            {
                "categories": [self.category.id],
                "count": 10,
            },
        )

        game = self.client.session["game"]

        self.assertEqual(
            game["category_ids"],
            [str(self.category.id)],
        )

        self.assertEqual(
            game["question_count"],
            10,
        )

        self.assertEqual(
            game["mode"],
            "normal",
        )


class QuestionViewTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="ネットワーク")

        self.term = Term.objects.create(
            category=self.category,
            word="TCP",
            description="説明",
        )

        self.user = User.objects.create_user(
            username="nagi",
            password="TestPassword123!",
        )

    # セッションが存在しない
    def test_no_session(self):
        response = self.client.get(reverse("question"))

        self.assertRedirects(
            response,
            reverse("game_error"),
        )

    # セッション作成
    def create_session(self):
        session = self.client.session

        session["question_ids"] = [self.term.id]
        session["current_index"] = 0

        session["current_question"] = {
            "hint_count": 0,
            "mistaken": False,
        }

        session["answers"] = []

        session["game"] = {
            "category_ids": [self.category.id],
        }

        session.save()

    # GET処理
    def test_question_get(self):
        self.create_session()

        response = self.client.get(reverse("question"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "terms/question.html")
        self.assertContains(response, self.term.description)

    # 未入力
    def test_question_empty_answer(self):
        self.create_session()

        response = self.client.post(
            reverse("question"),
            {
                "answer": "",
            },
        )

        self.assertContains(response, "回答を入力してください。")

    # 正解
    def test_question_correct_answer(self):
        self.create_session()

        response = self.client.post(
            reverse("question"),
            {
                "answer": "TCP",
            },
        )

        self.assertContains(response, "正解！")

    # 不正解
    def test_question_wrong_answer(self):
        self.create_session()

        response = self.client.post(
            reverse("question"),
            {
                "answer": "UDP",
            },
        )

        self.assertContains(response, "不正解です。")

    # ヒント全表示
    def test_question_show_answer_when_hint_finished(self):
        self.create_session()

        session = self.client.session
        session["current_question"]["hint_count"] = len(self.term.word)
        session.save()

        response = self.client.get(reverse("question"))

        self.assertContains(response, "正解は")

    # ミスカウント増加
    def test_question_increase_mistake_count(self):
        self.client.login(
            username="nagi",
            password="TestPassword123!",
        )

        self.create_session()

        self.client.post(
            reverse("question"),
            {
                "answer": "UDP",
            },
        )

        stat = UserTermStat.objects.get(
            user=self.user,
            term=self.term,
        )

        self.assertEqual(stat.mistake_count, 1)

    # ミスカウント減少
    def test_question_decrease_mistake_count(self):
        UserTermStat.objects.create(
            user=self.user,
            term=self.term,
            mistake_count=2,
        )

        self.client.login(
            username="nagi",
            password="TestPassword123!",
        )

        self.create_session()

        self.client.post(
            reverse("question"),
            {
                "answer": "TCP",
            },
        )

        stat = UserTermStat.objects.get(
            user=self.user,
            term=self.term,
        )

        self.assertEqual(stat.mistake_count, 1)

    # ミスカウント0でデータ削除
    def test_question_correct_delete_stat(self):
        self.client.login(
            username="nagi",
            password="TestPassword123!",
        )

        UserTermStat.objects.create(
            user=self.user,
            term=self.term,
            mistake_count=1,
        )

        session = self.client.session
        session["question_ids"] = [self.term.id]
        session["current_index"] = 0
        session["answers"] = []
        session["current_question"] = {
            "hint_count": 0,
            "mistaken": False,
        }
        session["game"] = {
            "category_ids": [str(self.category.id)],
            "question_count": 1,
        }
        session.save()

        self.client.post(
            reverse("question"),
            {
                "answer": "TCP",
            },
        )

        self.assertFalse(
            UserTermStat.objects.filter(
                user=self.user,
                term=self.term,
            ).exists()
        )


class NextQuestionViewTest(TestCase):
    # 準備
    def setUp(self):
        self.user = User.objects.create_user(
            username="nagi",
            password="TestPassword123!",
        )

        self.category = Category.objects.create(
            name="ネットワーク",
        )

        self.term = Term.objects.create(
            category=self.category,
            word="TCP",
            description="説明",
        )

    # question_idが存在しない
    def test_next_question_no_session(self):
        response = self.client.get(
            reverse("next_question"),
        )

        self.assertRedirects(
            response,
            reverse("game_error"),
        )

    # 次の問題へ進む
    def test_next_question(self):
        session = self.client.session

        session["question_ids"] = [self.term.id, self.term.id]
        session["current_index"] = 0
        session["answers"] = []
        session["current_question"] = {
            "hint_count": 0,
            "mistaken": False,
        }
        session.save()

        response = self.client.get(
            reverse("next_question"),
        )

        self.assertRedirects(
            response,
            reverse("question"),
        )

        session = self.client.session

        self.assertEqual(
            session["current_index"],
            1,
        )

        self.assertEqual(
            len(session["answers"]),
            1,
        )

    # ヒント・ミスなしは正解に
    def test_next_question_correct(self):
        session = self.client.session

        session["question_ids"] = [self.term.id, self.term.id]
        session["current_index"] = 0
        session["answers"] = []
        session["current_question"] = {
            "hint_count": 0,
            "mistaken": False,
        }
        session.save()

        self.client.get(reverse("next_question"))

        answers = self.client.session["answers"]

        self.assertTrue(
            answers[0]["is_correct"],
        )

    # ヒント使用は不正解
    def test_next_question_hint(self):
        session = self.client.session

        session["question_ids"] = [self.term.id, self.term.id]
        session["current_index"] = 0
        session["answers"] = []
        session["current_question"] = {
            "hint_count": 1,
            "mistaken": False,
        }
        session.save()

        self.client.get(reverse("next_question"))

        answers = self.client.session["answers"]

        self.assertFalse(
            answers[0]["is_correct"],
        )

    # 不正解で不正解
    def test_next_question_mistaken(self):
        session = self.client.session

        session["question_ids"] = [self.term.id, self.term.id]
        session["current_index"] = 0
        session["answers"] = []
        session["current_question"] = {
            "hint_count": 0,
            "mistaken": True,
        }
        session.save()

        self.client.get(reverse("next_question"))

        answers = self.client.session["answers"]

        self.assertFalse(
            answers[0]["is_correct"],
        )

    # current_questionがリセット
    def test_next_question_reset(self):
        session = self.client.session

        session["question_ids"] = [self.term.id, self.term.id]
        session["current_index"] = 0
        session["answers"] = []
        session["current_question"] = {
            "hint_count": 5,
            "mistaken": True,
        }
        session.save()

        self.client.get(reverse("next_question"))

        self.assertEqual(
            self.client.session["current_question"],
            {
                "hint_count": 0,
                "mistaken": False,
            },
        )

    # 最終問題でリザルトへ
    def test_next_question_finish(self):
        session = self.client.session

        session["question_ids"] = [self.term.id]
        session["current_index"] = 0
        session["answers"] = []
        session["current_question"] = {
            "hint_count": 0,
            "mistaken": False,
        }
        session["game"] = {
            "category_ids": [self.category.id],
            "question_count": 1,
        }
        session.save()

        self.client.login(
            username="nagi",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse("next_question"),
        )

        self.assertRedirects(
            response,
            reverse("result"),
        )

    def test_save_result_guest(self):
        session = self.client.session

        session["question_ids"] = [self.term.id]
        session["current_index"] = 0
        session["answers"] = [
            {
                "term_id": self.term.id,
                "is_correct": True,
                "hint_count": 0,
            }
        ]
        session["current_question"] = {
            "hint_count": 0,
            "mistaken": False,
        }
        session["game"] = {
            "category_ids": [str(self.category.id)],
            "question_count": 1,
            "mode": "normal",
        }
        session.save()

        self.client.get(reverse("next_question"))

        result = Result.objects.latest("id")

        self.assertIsNone(result.user)


class ResultViewTest(TestCase):
    # 準備
    def setUp(self):
        self.category = Category.objects.create(name="ネットワーク")

        self.term = Term.objects.create(
            category=self.category,
            word="TCP",
            description="説明",
        )

        self.result = Result.objects.create(
            question_count=1,
            correct_count=1,
            incorrect_count=0,
            accuracy=100,
        )

        self.result.categories.add(self.category)

    # result_idが存在しない
    def test_result_no_session(self):
        response = self.client.get(reverse("result"))

        self.assertRedirects(response, reverse("game_error"))

    # 正常表示
    def test_result_get(self):
        ResultDetail.objects.create(
            result=self.result,
            term=self.term,
            is_correct=True,
        )

        session = self.client.session
        session["result_id"] = self.result.id
        session["game"] = {
            "category_ids": [self.category.id],
        }
        session.save()

        response = self.client.get(reverse("result"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "terms/result.html")
        self.assertContains(response, "100")
        self.assertContains(response, "ネットワーク")

    # 間違えた問題表示
    def test_result_wrong_terms(self):
        ResultDetail.objects.create(
            result=self.result,
            term=self.term,
            is_correct=False,
        )

        session = self.client.session
        session["result_id"] = self.result.id
        session["game"] = {
            "category_ids": [self.category.id],
        }
        session.save()

        response = self.client.get(reverse("result"))

        self.assertContains(response, "TCP")

    # 全問正解
    def test_result_all_correct(self):
        ResultDetail.objects.create(
            result=self.result,
            term=self.term,
            is_correct=True,
        )

        session = self.client.session
        session["result_id"] = self.result.id
        session["game"] = {
            "category_ids": [self.category.id],
        }
        session.save()

        response = self.client.get(reverse("result"))

        self.assertContains(
            response,
            "間違えた用語はありません。",
        )

    # セッションからカテゴリ取得
    def test_result_category_from_session(self):
        ResultDetail.objects.create(
            result=self.result,
            term=self.term,
            is_correct=True,
        )

        session = self.client.session
        session["result_id"] = self.result.id
        session["game"] = {
            "category_ids": [self.category.id],
        }
        session.save()

        response = self.client.get(reverse("result"))

        self.assertContains(response, "ネットワーク")

    # Detailからカテゴリ取得（セッションがない場合）
    def test_result_category_from_details(self):
        ResultDetail.objects.create(
            result=self.result,
            term=self.term,
            is_correct=True,
        )

        session = self.client.session
        session["result_id"] = self.result.id
        session["game"] = {}
        session.save()

        response = self.client.get(reverse("result"))

        self.assertContains(response, "ネットワーク")

    # 存在しないresult_id
    def test_result_not_found(self):
        session = self.client.session
        session["result_id"] = 99999
        session.save()

        response = self.client.get(reverse("result"))

        self.assertEqual(response.status_code, 404)


class RetryViewTest(TestCase):
    # 準備
    def setUp(self):
        self.user = User.objects.create_user(
            username="nagi",
            password="TestPassword123!",
        )

        self.category = Category.objects.create(
            name="ネットワーク",
        )

        self.term = Term.objects.create(
            category=self.category,
            word="TCP",
            description="説明",
        )

    # gameがない
    def test_retry_no_game(self):
        response = self.client.get(
            reverse("retry"),
        )

        self.assertRedirects(
            response,
            reverse("game_error"),
        )

    # 通常モードでリトライ
    def test_retry_normal(self):
        session = self.client.session

        session["game"] = {
            "category_ids": [str(self.category.id)],
            "question_count": 10,
            "mode": "normal",
        }
        session.save()

        response = self.client.get(
            reverse("retry"),
        )

        self.assertRedirects(
            response,
            reverse("question"),
        )

    # リトライ時にセッションが初期化される
    def test_retry_normal_session(self):
        session = self.client.session

        session["game"] = {
            "category_ids": [str(self.category.id)],
            "question_count": 10,
            "mode": "normal",
        }
        session.save()

        self.client.get(reverse("retry"))

        session = self.client.session

        self.assertEqual(
            session["answers"],
            [],
        )

        self.assertEqual(
            session["current_question"],
            {
                "hint_count": 0,
                "mistaken": False,
            },
        )

        self.assertEqual(
            session["current_index"],
            0,
        )

        self.assertEqual(
            session["question_ids"],
            [self.term.id],
        )

    # 苦手問題モードでリトライ
    def test_retry_mistake(self):
        self.client.login(
            username="nagi",
            password="TestPassword123!",
        )

        UserTermStat.objects.create(
            user=self.user,
            term=self.term,
            mistake_count=2,
        )

        session = self.client.session

        session["game"] = {
            "mode": "mistake",
        }
        session.save()

        response = self.client.get(
            reverse("retry"),
        )

        self.assertRedirects(
            response,
            reverse("question"),
        )

    # 苦手問題モードで苦手問題のみ出題される
    def test_retry_mistake_question_ids(self):
        self.client.login(
            username="nagi",
            password="TestPassword123!",
        )

        UserTermStat.objects.create(
            user=self.user,
            term=self.term,
            mistake_count=2,
        )

        session = self.client.session

        session["game"] = {
            "mode": "mistake",
        }
        session.save()

        self.client.get(reverse("retry"))

        self.assertEqual(
            self.client.session["question_ids"],
            [self.term.id],
        )


class HintViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="nagi",
            password="TestPassword123!",
        )

        self.category = Category.objects.create(
            name="ネットワーク",
        )

        self.term = Term.objects.create(
            category=self.category,
            word="TCP",
            description="説明",
        )

    # ヒントを押すとhint_countが増える
    def test_show_hint(self):
        session = self.client.session

        session["question_ids"] = [self.term.id]
        session["current_index"] = 0
        session["current_question"] = {
            "hint_count": 0,
            "mistaken": False,
        }
        session.save()

        response = self.client.get(reverse("show_hint"))

        self.assertRedirects(
            response,
            reverse("question"),
        )

        self.assertEqual(
            self.client.session["current_question"]["hint_count"],
            1,
        )

    # ログイン中ならmistake_countが増える
    def test_show_hint_login(self):
        self.client.login(
            username="nagi",
            password="TestPassword123!",
        )

        session = self.client.session

        session["question_ids"] = [self.term.id]
        session["current_index"] = 0
        session["current_question"] = {
            "hint_count": 0,
            "mistaken": False,
        }
        session.save()

        self.client.get(reverse("show_hint"))

        stat = UserTermStat.objects.get(
            user=self.user,
            term=self.term,
        )

        self.assertEqual(
            stat.mistake_count,
            1,
        )

    # ログインしていないなら統計は作られない
    def test_show_hint_guest(self):
        session = self.client.session

        session["question_ids"] = [self.term.id]
        session["current_index"] = 0
        session["current_question"] = {
            "hint_count": 0,
            "mistaken": False,
        }
        session.save()

        self.client.get(reverse("show_hint"))

        self.assertFalse(
            UserTermStat.objects.exists(),
        )

    # 2回押してもmistake_countは増えない
    def test_show_hint_only_once(self):
        self.client.login(
            username="nagi",
            password="TestPassword123!",
        )

        session = self.client.session

        session["question_ids"] = [self.term.id]
        session["current_index"] = 0
        session["current_question"] = {
            "hint_count": 0,
            "mistaken": False,
        }
        session.save()

        self.client.get(reverse("show_hint"))
        self.client.get(reverse("show_hint"))

        stat = UserTermStat.objects.get(
            user=self.user,
            term=self.term,
        )

        self.assertEqual(
            stat.mistake_count,
            1,
        )

    # mistakenがTrueになる
    def test_show_hint_set_mistaken(self):
        self.client.login(
            username="nagi",
            password="TestPassword123!",
        )

        session = self.client.session

        session["question_ids"] = [self.term.id]
        session["current_index"] = 0
        session["current_question"] = {
            "hint_count": 0,
            "mistaken": False,
        }
        session.save()

        self.client.get(reverse("show_hint"))

        self.assertTrue(self.client.session["current_question"]["mistaken"])


class MypageViewTest(TestCase):
    # login_requiredのテスト
    def test_mypage_login_required(self):
        response = self.client.get(reverse("mypage"))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('mypage')}",
        )

    # 準備
    def setUp(self):
        self.category = Category.objects.create(name="ネットワーク")

        self.term = Term.objects.create(
            category=self.category,
            word="TCP",
            description="説明",
        )

        self.user = User.objects.create_user(
            username="nagi",
            password="TestPassword123!",
        )

    # ログイン済みならマイページ表示
    def test_mypage_get(self):
        self.client.login(
            username="nagi",
            password="TestPassword123!",
        )

        response = self.client.get(reverse("mypage"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "terms/mypage.html")

    # プレイ履歴取得
    def test_mypage_results(self):
        Result.objects.create(
            user=self.user,
            question_count=10,
            correct_count=8,
            incorrect_count=2,
            accuracy=80,
        )

        Result.objects.create(
            user=self.user,
            question_count=5,
            correct_count=5,
            incorrect_count=0,
            accuracy=100,
        )

        self.client.login(
            username="nagi",
            password="TestPassword123!",
        )

        response = self.client.get(reverse("mypage"))

        self.assertEqual(
            len(response.context["results"]),
            2,
        )

    # 苦手問題ランキング取得
    def test_mypage_rankings(self):
        UserTermStat.objects.create(
            user=self.user,
            term=self.term,
            mistake_count=3,
        )

        self.client.login(
            username="nagi",
            password="TestPassword123!",
        )

        response = self.client.get(reverse("mypage"))

        self.assertEqual(
            len(response.context["rankings"]),
            1,
        )

    # ランキングがミスカウント順になってるか
    def test_mypage_rankings_order(self):
        term2 = Term.objects.create(
            category=self.category,
            word="UDP",
            description="説明2",
        )

        UserTermStat.objects.create(
            user=self.user,
            term=self.term,
            mistake_count=2,
        )

        UserTermStat.objects.create(
            user=self.user,
            term=term2,
            mistake_count=5,
        )

        self.client.login(
            username="nagi",
            password="TestPassword123!",
        )

        response = self.client.get(reverse("mypage"))

        rankings = response.context["rankings"]

        self.assertEqual(rankings[0].term.word, "UDP")
        self.assertEqual(rankings[1].term.word, "TCP")

    # 他人のデータが表示されない
    def test_mypage_only_my_results(self):
        other = User.objects.create_user(
            username="other",
            password="Password123!",
        )

        Result.objects.create(
            user=self.user,
            question_count=1,
            correct_count=1,
            incorrect_count=0,
            accuracy=100,
        )

        Result.objects.create(
            user=other,
            question_count=99,
            correct_count=99,
            incorrect_count=0,
            accuracy=100,
        )

        self.client.login(
            username="nagi",
            password="TestPassword123!",
        )

        response = self.client.get(reverse("mypage"))

        self.assertEqual(
            len(response.context["results"]),
            1,
        )

    # 他人の苦手ランキングが表示されない
    def test_mypage_only_my_rankings(self):
        other = User.objects.create_user(
            username="other",
            password="Password123!",
        )

        UserTermStat.objects.create(
            user=self.user,
            term=self.term,
            mistake_count=2,
        )

        UserTermStat.objects.create(
            user=other,
            term=self.term,
            mistake_count=99,
        )

        self.client.login(
            username="nagi",
            password="TestPassword123!",
        )

        response = self.client.get(reverse("mypage"))

        self.assertEqual(
            len(response.context["rankings"]),
            1,
        )

        self.assertEqual(
            response.context["rankings"][0].user,
            self.user,
        )


class MistakeQuizViewTest(TestCase):
    # 準備
    def setUp(self):
        self.user = User.objects.create_user(
            username="nagi",
            password="TestPassword123!",
        )

        self.category = Category.objects.create(
            name="ネットワーク",
        )

        self.term = Term.objects.create(
            category=self.category,
            word="TCP",
            description="説明",
        )

    # 苦手問題が存在しない
    def test_mistake_quiz_no_terms(self):
        self.client.login(
            username="nagi",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse("mistake_quiz"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "terms/top.html")
        self.assertContains(
            response,
            "間違えた問題がありません。",
        )

    # 苦手問題が存在する
    def test_mistake_quiz_redirect(self):
        self.client.login(
            username="nagi",
            password="TestPassword123!",
        )

        UserTermStat.objects.create(
            user=self.user,
            term=self.term,
            mistake_count=2,
        )

        response = self.client.get(
            reverse("mistake_quiz"),
        )

        self.assertRedirects(
            response,
            reverse("question"),
        )

    # セッションが正しく作られる
    def test_mistake_quiz_session(self):
        self.client.login(
            username="nagi",
            password="TestPassword123!",
        )

        UserTermStat.objects.create(
            user=self.user,
            term=self.term,
            mistake_count=2,
        )

        self.client.get(reverse("mistake_quiz"))

        session = self.client.session

        self.assertEqual(
            session["current_index"],
            0,
        )

        self.assertEqual(
            session["answers"],
            [],
        )

        self.assertEqual(
            session["question_ids"],
            [self.term.id],
        )

        self.assertEqual(
            session["current_question"],
            {
                "hint_count": 0,
                "mistaken": False,
            },
        )

    # ゲームモードが設定される
    def test_mistake_quiz_game_session(self):
        self.client.login(
            username="nagi",
            password="TestPassword123!",
        )

        UserTermStat.objects.create(
            user=self.user,
            term=self.term,
            mistake_count=2,
        )

        self.client.get(reverse("mistake_quiz"))

        game = self.client.session["game"]

        self.assertEqual(
            game["mode"],
            "mistake",
        )

        self.assertEqual(
            game["question_count"],
            1,
        )
        # 苦手問題時はカテゴリidの初期値が空なので
        self.assertEqual(
            game["category_ids"],
            [],
        )

    # ミステイクが０の問題は出題されない
    def test_mistake_count_zero_not_selected(self):
        self.client.login(
            username="nagi",
            password="TestPassword123!",
        )

        term2 = Term.objects.create(
            category=self.category,
            word="UDP",
            description="説明2",
        )

        UserTermStat.objects.create(
            user=self.user,
            term=self.term,
            mistake_count=2,
        )

        UserTermStat.objects.create(
            user=self.user,
            term=term2,
            mistake_count=0,
        )

        self.client.get(reverse("mistake_quiz"))

        session = self.client.session

        self.assertEqual(
            session["question_ids"],
            [self.term.id],
        )


class LogoutViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="nagi",
            password="TestPassword123!",
        )

    # ログアウトでトップに戻る
    def test_logout(self):
        self.client.login(
            username="nagi",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse("logout"),
        )

        self.assertRedirects(
            response,
            reverse("top"),
        )

    # ログアウト後の処理が正常
    def test_logout_user(self):
        self.client.login(
            username="nagi",
            password="TestPassword123!",
        )

        self.client.get(reverse("logout"))

        response = self.client.get(reverse("mypage"))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('mypage')}",
        )
