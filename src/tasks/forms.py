from django import forms
from .models import TaskSolution



class TaskSolutionForm(forms.ModelForm):
    
    code_src = forms.CharField(widget=forms.Textarea)
    
    def __init__(self, *args, **kwargs):
        super(TaskSolutionForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['code_src'].initial = self.get_code_src(self.instance)
            self.fields['code_src'].widget.attrs['id'] = 'codeEditor'
            for field in self.fields:
                if field in self.Meta.readonly_fields:
                    self.fields[field].widget.attrs['readonly'] = 'readonly'
    
    def get_code_src(self, obj):
        if obj.code:
            with open(obj.code.path, 'r') as file:
                return file.read()
        return " "
     
    class Meta:
        model = TaskSolution
        fields = ["task", "code_src", "score", "tries"]
        readonly_fields = ('task', 'team', 'submitted_at','tries', 'code_src')
        
              
    class Media:
        js = ('editor/js/codemirror.min.js','editor/js/clike.min.js','editor/js/editor.js')
        css = {
            'all': ('editor/css/codemirror.min.css','editor/css/monokai.min.css'),
        }
  