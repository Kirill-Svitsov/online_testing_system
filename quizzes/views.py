from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.forms import formset_factory
from django.views.generic import ListView
from django.db.models import Q
import json

from .models import *
from .forms import AnswerForm


class AllTestsView(ListView):
    """
    Вью домешней страницы со всеми тестами.
    """
    template_name = 'quizzes/tests.html'
    context_object_name = 'tests'

    def get_queryset(self):
        return Test.objects.all()


@login_required
def quizz_detail(request, pk: int):
    """
    Представление конкретного теста.
    :param request:
    :param pk:
    :return:
    """
    test = get_object_or_404(Test, pk=pk)
    test_questions = TestQuestion.objects.filter(test=test).select_related('question').order_by('order')
    AnswerFormSet = formset_factory(AnswerForm, extra=0)
    if request.method == 'POST':
        formset = AnswerFormSet(request.POST, prefix='answers')
        if formset.is_valid():
            for i, form in enumerate(formset):
                question = test_questions[i].question
                # Для вопросов с множественным выбором получаем список выбранных ответов
                if question.question_type == 'multiple':
                    answer = request.POST.getlist(f'{form.prefix}-answer')
                else:
                    answer = form.cleaned_data.get('answer')
                UserAnswer.objects.update_or_create(
                    user=request.user,
                    test=test,
                    question=question,
                    defaults={'answer': answer}
                )
            return redirect('quizzes:test_result', pk=test.id)
    else:
        initial_data = [{
            'question_id': tq.question.id,
            'question_text': tq.question.text,
            'question_type': tq.question.question_type,
            'choices': json.dumps(tq.question.choices or []),
        } for tq in test_questions]
        formset = AnswerFormSet(initial=initial_data, prefix='answers')

    return render(request, 'quizzes/test_detail.html', {
        'test': test,
        'formset': formset,
    })


@login_required
def quizz_result(request, pk: int):
    """
    Представление результатов конкретного теста
    :param request:
    :param pk:
    :return:
    """
    test = get_object_or_404(Test, pk=pk)
    result = TestResult.objects.filter(user=request.user, test=test).first()
    if not result:
        return redirect('some_error_page')
    detailed_results = result.calculate_score()
    context = {
        'test': test,
        'result': result,
        'detailed_results': detailed_results,
        'correct_count': sum(1 for r in detailed_results if r['is_correct']),
        'incorrect_count': sum(1 for r in detailed_results if not r['is_correct']),
    }
    return render(request, 'quizzes/test_result.html', context)


class CompletedTestsView(ListView):
    """
    Представление всех пройденных тестов.
    """
    template_name = 'quizzes/completed_tests.html'
    context_object_name = 'completed_tests'

    def get_queryset(self):
        return TestResult.objects.filter(user=self.request.user).select_related('test')


def search_tests(request):
    query = request.GET.get('q', '')
    if query:
        tests = Test.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        ).distinct()
    else:
        tests = Test.objects.none()
    context = {
        'tests': tests,
        'query': query,
        'results_count': tests.count()
    }
    return render(request, 'quizzes/search_results.html', context)
