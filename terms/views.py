import random
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from .models import Category, Term, Result, ResultDetail, UserTermStat
from .forms import SignUpForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required


# from django.http import HttpResponse
from .utils import normalize, make_hint, is_correct_answer


def top(request, message=None, message_type=None):
    categories = Category.objects.annotate(term_count=Count("terms"))

    return render(
        request,
        "terms/top.html",
        {
            "categories": categories,
            "message": message,
            "message_type": message_type,
        },
    )


def start(request):
    category_ids = request.GET.getlist("categories")
    count = int(request.GET.get("count", 10))

    if not category_ids:
        return top(
            request,
            message="カテゴリを1つ以上選択してください。",
            message_type="danger",
        )

    if count not in [10, 20, 30]:
        return redirect("game_error")

    # 回答リセット
    request.session["answers"] = []
    request.session["current_question"] = {
        "hint_count": 0,
        "mistaken": False,
    }

    # 選択した分野の問題を取得
    terms = list(Term.objects.filter(category_id__in=category_ids))

    # 問題をシャッフル
    random.shuffle(terms)

    # 問題数だけ取り出す
    terms = terms[:count]

    # セッションに保存
    request.session["question_ids"] = [term.id for term in terms]
    request.session["current_index"] = 0
    request.session["game"] = {
        "category_ids": category_ids,
        "question_count": count,
        "mode": "normal",
    }

    return redirect("question")


# セッションから取得
def question(request):
    question_ids = request.session.get("question_ids", [])
    current_index = request.session.get("current_index", 0)

    if not question_ids:
        return redirect("game_error")

    question = Term.objects.get(id=question_ids[current_index])

    message = None
    message_type = None
    show_next_button = False
    hint = ""
    keep_message = False

    current_question = request.session["current_question"]

    hint = make_hint(
        question.word,
        current_question["hint_count"],
    )

    if current_question["hint_count"] >= len(question.word):
        show_next_button = True
        message = f"不正解です。正解は『{question.word}』です。"
        message_type = "danger"
        keep_message = True

    if request.method == "POST" and not show_next_button:
        answer = normalize(request.POST.get("answer", ""))

        if not answer:
            message = "回答を入力してください。"
            message_type = "danger"

        elif is_correct_answer(question, answer):
            message = f"正解！『{question.word}』です。"
            message_type = "success"
            show_next_button = True

            if request.user.is_authenticated:
                stat = UserTermStat.objects.filter(
                    user=request.user,
                    term=question,
                ).first()

                if stat:
                    if stat.mistake_count > 1:
                        stat.mistake_count -= 1
                        stat.save()
                    else:
                        stat.delete()

        else:
            message = "不正解です。"
            message_type = "danger"
            keep_message = False

            if not current_question.get("mistaken", False):
                current_question["mistaken"] = True
                request.session["current_question"] = current_question

                if request.user.is_authenticated:
                    stat, _ = UserTermStat.objects.get_or_create(
                        user=request.user,
                        term=question,
                    )
                    stat.mistake_count += 1
                    stat.save()

    game = request.session.get("game", {})
    category_ids = game.get("category_ids", [])
    categories = Category.objects.filter(id__in=category_ids)
    if categories.exists():
        category_label = "・".join(categories.values_list("name", flat=True))
    else:
        category_label = question.category.name

    answers = request.session.get("answers", [])
    answered_count = len(answers)
    correct_answered = sum(1 for answer in answers if answer["is_correct"])
    session_accuracy = (
        round(correct_answered / answered_count * 100) if answered_count > 0 else 0
    )

    return render(
        request,
        "terms/question.html",
        {
            "question": question,
            "message": message,
            "message_type": message_type,
            "show_next_button": show_next_button,
            "hint": hint,
            "hint_count": current_question["hint_count"],
            "keep_message": keep_message,
            "current": current_index + 1,
            "total": len(question_ids),
            "remaining": len(question_ids) - current_index - 1,
            "category_label": category_label,
            "answered_count": answered_count,
            "correct_answered": correct_answered,
            "session_accuracy": session_accuracy,
        },
    )


def show_hint(request):
    current_question = request.session["current_question"]

    if request.user.is_authenticated and not current_question.get("mistaken", False):
        question_ids = request.session["question_ids"]
        current_index = request.session["current_index"]

        question = Term.objects.get(id=question_ids[current_index])

        stat, _ = UserTermStat.objects.get_or_create(
            user=request.user,
            term=question,
        )
        stat.mistake_count += 1
        stat.save()

        current_question["mistaken"] = True

    current_question["hint_count"] += 1

    request.session["current_question"] = current_question

    return redirect("question")


def next_question(request):
    question_ids = request.session.get("question_ids", [])
    if not question_ids:
        return redirect("game_error")

    current_index = request.session.get("current_index", 0)

    question = Term.objects.get(id=question_ids[current_index])

    current_question = request.session["current_question"]
    hint_count = current_question["hint_count"]

    answers = request.session.get("answers", [])

    answers.append(
        {
            "term_id": question.id,
            "is_correct": (not current_question["mistaken"] and hint_count == 0),
            "hint_count": hint_count,
        }
    )

    request.session["answers"] = answers

    # 次の問題用にリセット
    request.session["current_question"] = {
        "hint_count": 0,
        "mistaken": False,
    }

    request.session["current_index"] += 1

    if request.session["current_index"] >= len(question_ids):
        save_result(request)
        return redirect("result")

    return redirect("question")


def save_result(request):
    answers = request.session.get("answers", [])

    question_count = len(answers)
    correct_count = sum(1 for answer in answers if answer["is_correct"])
    incorrect_count = question_count - correct_count

    accuracy = round(correct_count / question_count * 100) if question_count > 0 else 0

    if request.user.is_authenticated:
        result = Result.objects.create(
            user=request.user,
            question_count=question_count,
            correct_count=correct_count,
            incorrect_count=incorrect_count,
            accuracy=accuracy,
        )

        category_ids = request.session["game"]["category_ids"]
        result.categories.set(category_ids)
    else:
        # リザルト画面を表示するため（後でセッションに変更）
        result = Result.objects.create(
            question_count=question_count,
            correct_count=correct_count,
            incorrect_count=incorrect_count,
            accuracy=accuracy,
        )

    details = []

    for answer in answers:
        details.append(
            ResultDetail(
                result=result,
                term_id=answer["term_id"],
                is_correct=answer["is_correct"],
                hint_count=answer["hint_count"],
            )
        )

    ResultDetail.objects.bulk_create(details)

    request.session["result_id"] = result.id


def result(request):
    result_id = request.session.get("result_id")

    if not result_id:
        return redirect("game_error")

    result = get_object_or_404(Result, id=result_id)

    details = list(
        result.details.select_related(
            "term",
            "term__category",
        )
    )

    game = request.session.get("game", {})
    category_ids = game.get("category_ids", [])
    categories = Category.objects.filter(id__in=category_ids)
    if categories.exists():
        category_label = "・".join(categories.values_list("name", flat=True))
    else:
        category_names = {detail.term.category.name for detail in details}
        category_label = "・".join(sorted(category_names))

    wrong_details = [
        {"index": index, "term": detail.term}
        for index, detail in enumerate(details, start=1)
        if not detail.is_correct
    ]

    return render(
        request,
        "terms/result.html",
        {
            "total": result.question_count,
            "correct": result.correct_count,
            "incorrect": result.incorrect_count,
            "accuracy": result.accuracy,
            "details": details,
            "wrong_details": wrong_details,
            "category_label": category_label,
        },
    )


def retry(request):
    game = request.session.get("game")
    if not game:
        return redirect("game_error")

    request.session["answers"] = []
    request.session["current_question"] = {
        "hint_count": 0,
        "mistaken": False,
    }

    # 間違えた問題モード
    if game.get("mode") == "mistake":
        terms = list(
            Term.objects.filter(
                user_stats__user=request.user,
                user_stats__mistake_count__gt=0,
            ).distinct()
        )
        random.shuffle(terms)

    # 通常モード
    else:
        category_ids = game["category_ids"]
        count = game["question_count"]

        terms = list(Term.objects.filter(category_id__in=category_ids))
        random.shuffle(terms)
        terms = terms[:count]

    request.session["question_ids"] = [term.id for term in terms]
    request.session["current_index"] = 0

    return redirect("question")


def game_error(request):
    return render(request, "game_error.html")


def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("login")

    else:
        form = SignUpForm()

    return render(
        request,
        "terms/signup.html",
        {
            "form": form,
        },
    )


def login_view(request):
    message = None

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not username or not password:
            message = "ユーザー名とパスワードを入力してください。"

        else:
            user = authenticate(
                request,
                username=username,
                password=password,
            )

            if user is not None:
                login(request, user)
                return redirect("top")

            message = "ユーザー名またはパスワードが違います。"

    return render(
        request,
        "terms/login.html",
        {
            "message": message,
        },
    )


def logout_view(request):
    logout(request)
    return redirect("top")


@login_required
def mypage(request):
    results = Result.objects.filter(user=request.user).order_by("-created_at")

    rankings = (
        UserTermStat.objects.filter(user=request.user)
        .select_related("term")
        .order_by("-mistake_count")[:10]
    )

    return render(
        request,
        "terms/mypage.html",
        {
            "results": results,
            "rankings": rankings,
        },
    )


def mistake_quiz(request):

    terms = list(
        Term.objects.filter(
            user_stats__user=request.user,
            user_stats__mistake_count__gt=0,
        ).distinct()
    )

    if not terms:
        return top(
            request,
            message="間違えた問題がありません。",
            message_type="info",
        )

    random.shuffle(terms)

    request.session["answers"] = []
    request.session["current_question"] = {
        "hint_count": 0,
        "mistaken": False,
    }

    request.session["question_ids"] = [term.id for term in terms]
    request.session["current_index"] = 0

    request.session["game"] = {
        "category_ids": [],
        "question_count": len(terms),
        "mode": "mistake",
    }

    return redirect("question")
