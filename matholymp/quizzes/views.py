from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Quiz, Question, Option
from django.utils import timezone


def home(request):
    quizzes = Quiz.objects.all()
    return render(request, 'quizzes/home.html', {'quizzes': quizzes})


@login_required
def take_quiz(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    if request.method == 'POST':
        score = 0
        for question in quiz.questions.all():
            selected = request.POST.get(str(question.id))
            if selected and question.options.filter(id=selected, is_correct=True).exists():
                score += 1
        return render(request, 'quizzes/result.html', {'quiz': quiz, 'score': score})
    return render(request, 'quizzes/quiz.html', {'quiz': quiz})
