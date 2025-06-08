from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import formset_factory
from django.views.generic import ListView, View
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
import json
import csv
from io import TextIOWrapper

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


class UploadCSVView(View):
    template_name = 'quizzes/upload_csv.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        if 'csv_file' not in request.FILES:
            messages.error(request, "Файл не выбран")
            return redirect('quizzes:home')
        try:
            file = TextIOWrapper(request.FILES['csv_file'].file, encoding='utf-8-sig')
            created_tests = self.process_csv(file)
            messages.success(request, f"Успешно создано {created_tests} тестов!")
        except Exception as e:
            messages.error(request, f"Ошибка: {str(e)}")
        return redirect('quizzes:home')

    def process_csv(self, file):
        reader = csv.DictReader(file, delimiter=';')
        created_count = 0
        for row in reader:
            # Обрабатываем тест (создаем или получаем существующий)
            test, created = Test.objects.get_or_create(
                title=row['test_title'].strip(),
                defaults={'description': row.get('test_description', '').strip()}
            )
            if created:
                created_count += 1
            # Обрабатываем вопрос
            question = Question.objects.create(
                text=row['question_text'].strip(),
                question_type=row['question_type'].strip(),
                choices=[c.strip() for c in row['choices'].split('|')],
                correct_answers=[c.strip() for c in row['correct_answers'].split('|')]
            )
            # Связываем вопрос с тестом
            TestQuestion.objects.create(
                test=test,
                question=question,
                order=int(row.get('question_order', 0))
            )

        return created_count


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('quizzes:login')
    else:
        form = UserCreationForm()
    return render(request, 'quizzes/auth/register.html', {'form': form})
