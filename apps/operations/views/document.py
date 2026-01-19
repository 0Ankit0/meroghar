from django.views.generic import ListView, DetailView, CreateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from apps.operations.models import Document
from django import forms

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'file', 'content_type', 'object_id']
        widgets = {
             'content_type': forms.HiddenInput(),
             'object_id': forms.HiddenInput(),
        }

class DocumentListView(LoginRequiredMixin, ListView):
    model = Document
    template_name = 'operations/document_list.html'
    context_object_name = 'documents'
    paginate_by = 20

    def get_queryset(self):
        if self.request.user.organization:
            return Document.objects.filter(organization=self.request.user.organization).order_by('-created_at')
        return Document.objects.none()

class DocumentCreateView(LoginRequiredMixin, CreateView):
    model = Document
    template_name = 'operations/document_form.html'
    fields = ['title', 'file']
    success_url = reverse_lazy('operations:document_list')

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        form.instance.uploaded_by = self.request.user
        return super().form_valid(form)

class DocumentDetailView(LoginRequiredMixin, DetailView):
    model = Document
    template_name = 'operations/document_detail.html'
    context_object_name = 'document'

    def get_queryset(self):
        if self.request.user.organization:
            return Document.objects.filter(organization=self.request.user.organization)
        return Document.objects.none()

class DocumentDeleteView(LoginRequiredMixin, DeleteView):
    model = Document
    template_name = 'operations/document_confirm_delete.html'
    success_url = reverse_lazy('operations:document_list')

    def get_queryset(self):
         if self.request.user.organization:
            return Document.objects.filter(organization=self.request.user.organization)
         return Document.objects.none()
