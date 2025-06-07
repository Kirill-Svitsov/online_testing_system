from django.contrib import admin
from .models import Test, Question, TestQuestion, UserAnswer, TestResult


class TestQuestionInline(admin.TabularInline):
    model = TestQuestion
    extra = 1
    ordering = ('order',)


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    inlines = (TestQuestionInline,)
    list_display = ('title', 'question_count')

    def question_count(self, obj):
        return obj.test_questions.count()

    question_count.short_description = 'Количество вопросов'


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text_short', 'question_type')
    fields = ('text', 'question_type', 'choices', 'correct_answers')

    def text_short(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text

    text_short.short_description = 'Текст вопроса'


@admin.register(TestQuestion)
class TestQuestionAdmin(admin.ModelAdmin):
    list_display = ('test', 'question', 'order')
    list_filter = ('test',)
    ordering = ('test', 'order')


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('user', 'test', 'question', 'created_at')
    list_filter = ('test', 'user')
    search_fields = ('user__username', 'test__title')


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'test', 'score', 'is_completed', 'completed_at')
    list_filter = ('test', 'is_completed')
    search_fields = ('user__username', 'test__title')
