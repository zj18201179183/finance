from .models import *

def get_all_subject(user_obj):
    all_subjects = {}
    for sub_obj in Subject.objects.filter(village=None):
        if sub_obj.get_subject_type_display() not in all_subjects:
            all_subjects[sub_obj.get_subject_type_display()] = []
        all_subjects[sub_obj.get_subject_type_display()].append({
            'id': sub_obj.id,
            'subject_num': sub_obj.subject_num,
            'subject_name': sub_obj.subject_name,
            'balance_type': sub_obj.get_balance_type_display(),
            'num' : sub_obj.subjectofaccounts.num if hasattr(sub_obj, 'subjectofaccounts') else 0,
            'money' : sub_obj.subjectofaccounts.money if hasattr(sub_obj, 'subjectofaccounts') else 0,
        })

    for sub_obj in Subject.objects.filter(village=user_obj.village):
        if sub_obj.get_subject_type_display() not in all_subjects:
            all_subjects[sub_obj.get_subject_type_display()] = []
        all_subjects[sub_obj.get_subject_type_display()].append({
            'id': sub_obj.id,
            'subject_num': sub_obj.subject_num,
            'subject_name': sub_obj.subject_name,
            'balance_type': sub_obj.get_balance_type_display(),
            'num' : sub_obj.subjectofaccounts.num if hasattr(sub_obj, 'subjectofaccounts') else 0,
            'money' : sub_obj.subjectofaccounts.money if hasattr(sub_obj, 'subjectofaccounts') else 0,
        })
    return all_subjects