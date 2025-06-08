from django.contrib import admin
from .models import Test, Question, TestQuestion, UserAnswer, TestResult


class TestQuestionInline(admin.TabularInline):
    model = TestQuestion
    extra = 1
    ordering = ('order',)
    show_change_link = True
    fields = ('question', 'order', 'question_type_display')
    readonly_fields = ('question_type_display',)

    def question_type_display(self, obj):
        return obj.question.get_question_type_display()

    question_type_display.short_description = 'Тип вопроса'


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    inlines = (TestQuestionInline,)
    list_display = ('title', 'question_count')
    search_fields = ('title', 'description')

    def question_count(self, obj):
        return obj.test_questions.count()

    question_count.short_description = 'Количество вопросов'


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'text_short', 'question_type')
    list_display_links = ('id', 'text_short')
    list_filter = ('question_type',)
    search_fields = ('text', 'id')
    fields = ('text', 'question_type', 'choices', 'correct_answers')

    def text_short(self, obj):
        return f"{obj.text[:50]}..." if len(obj.text) > 50 else obj.text

    text_short.short_description = 'Текст вопроса'


@admin.register(TestQuestion)
class TestQuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'test', 'question', 'question_type', 'order')
    list_filter = ('test', 'question__question_type')
    search_fields = (
        'test__title',
        'question__text',
        'question__id',
        'test__id'
    )
    ordering = ('test', 'order')
    autocomplete_fields = ('test', 'question')

    def question_type(self, obj):
        return obj.question.get_question_type_display()

    question_type.short_description = 'Тип вопроса'


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    # Отображение в списке
    list_display = ('id', 'user', 'test', 'question_short', 'answer_preview', 'created_at')
    list_filter = ('test', 'user', 'created_at')
    search_fields = (
        'user__username',
        'test__title',
        'question__text',
        'question__id',
        'test__id'
    )
    autocomplete_fields = ('test', 'question', 'user')

    # Настройки для страницы редактирования
    readonly_fields = ('question_id', 'question_full_text', 'created_at', 'answer_preview')
    fieldsets = (
        (None, {
            'fields': ('user', 'test', 'question')
        }),
        ('Ответ', {
            'fields': ('answer',),
        }),
        ('Детали вопроса', {
            'fields': ('question_id', 'question_full_text'),
            'classes': ('collapse',)
        }),
        ('Дополнительная информация', {
            'fields': ('created_at', 'answer_preview'),
            'classes': ('collapse',)
        }),
    )

    def question_short(self, obj):
        return obj.question.text[:50] + '...' if obj.question and len(obj.question.text) > 50 else (
            obj.question.text if obj.question else '-')

    question_short.short_description = 'Вопрос'

    def answer_preview(self, obj):
        return str(obj.answer)[:100] + '...' if len(str(obj.answer)) > 100 else str(obj.answer)

    answer_preview.short_description = 'Превью ответа'

    def question_id(self, obj):
        return obj.question.id if obj.question else '-'

    question_id.short_description = 'ID вопроса'

    def question_full_text(self, obj):
        return obj.question.text if obj.question else '-'

    question_full_text.short_description = 'Текст вопроса'


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'test',
        'score',
        'is_completed',
        'completed_at'
    )
    list_filter = ('test', 'is_completed')
    search_fields = ('user__username', 'test__title', 'test__id')
