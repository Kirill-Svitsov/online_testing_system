from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import formset_factory
from django.views.generic import ListView, View
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
import json


from .models import *
from .forms import AnswerForm
from quizzes.services.csv_importer import CSVTestImporter


class AllTestsView(ListView):
    """
    Вью для отображения всех тестов с пагинацией.
    """
    template_name = 'quizzes/tests.html'
    context_object_name = 'tests'
    paginate_by = 10
    model = Test

    def get_queryset(self):
        """
        Возвращает queryset всех тестов, отсортированных по названию.
        """
        return Test.objects.all().order_by('title')


@login_required(login_url='quizzes:login')
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
            # Сохраняем ответы пользователя
            for i, form in enumerate(formset):
                question = test_questions[i].question
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
            # Создаем или обновляем результат теста
            test_result, created = TestResult.objects.get_or_create(
                user=request.user,
                test=test,
                defaults={'is_completed': True}
            )
            # Пересчитываем результат
            detailed_results = test_result.calculate_score()
            correct_count = sum(1 for r in detailed_results if r['is_correct'])
            total_questions = test_questions.count()
            test_result.score = (correct_count / total_questions) * 100 if total_questions > 0 else 0
            test_result.save()
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


@login_required(login_url='quizzes:login')
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
        return redirect('quizzes:home')
    detailed_results = result.calculate_score()
    context = {
        'test': test,
        'result': result,
        'detailed_results': detailed_results,
        'correct_count': sum(1 for r in detailed_results if r['is_correct']),
        'incorrect_count': sum(1 for r in detailed_results if not r['is_correct']),
    }
    return render(request, 'quizzes/test_result.html', context)


class CompletedTestsView(LoginRequiredMixin, ListView):
    """
    Представление всех пройденных тестов.
    """
    template_name = 'quizzes/completed_tests.html'
    context_object_name = 'completed_tests'
    login_url = 'quizzes:login'

    def get_queryset(self):
        return TestResult.objects.filter(user=self.request.user).select_related('test')


def search_tests(request):
    """
    Обработчик поисковой строки.
    :param request:
    :return:
    """
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


class UploadCSVView(LoginRequiredMixin, View):
    template_name = 'quizzes/upload_csv.html'
    login_url = 'quizzes:login'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        if 'csv_file' not in request.FILES:
            messages.error(request, "Файл не выбран")
            return redirect('quizzes:home')
        try:
            update_existing = request.POST.get('update_existing') == 'on'
            importer = CSVTestImporter(update_existing=update_existing)
            stats = importer.process_csv(request.FILES['csv_file'])
            if update_existing:
                message = (
                    f"Результат импорта:<br>"
                    f"- Создано тестов: {stats['tests_created']}<br>"
                    f"- Обновлено тестов: {stats['tests_updated']}<br>"
                    f"- Добавлено вопросов: {stats['questions_created']}<br>"
                    f"- Переиспользовано вопросов: {stats['questions_reused']}<br>"
                    f"- Удалено старых вопросов: {stats['questions_removed']}<br>"
                    f"- Объединено дубликатов: {stats['duplicates_resolved']}"
                )
            else:
                message = (
                    f"Результат импорта:<br>"
                    f"- Создано тестов: {stats['tests_created']}<br>"
                    f"- Добавлено вопросов: {stats['questions_created']}<br>"
                    f"- Переиспользовано вопросов: {stats['questions_reused']}"
                )

            messages.success(request, message)
        except Exception as e:
            messages.error(request, f"Ошибка: {str(e)}")
        return render(request, self.template_name)


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('quizzes:login')
    else:
        form = UserCreationForm()
    return render(request, 'quizzes/auth/register.html', {'form': form})
