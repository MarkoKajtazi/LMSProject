# chat/acl.py
from users.models import Professor, TeachingAssistant, Student
from courses.models import Enrollment

def user_can_access_course_room(user, course) -> bool:
    if not user.is_authenticated:
        return False

    # Professor of this course? (support either course.instructor or course.professor)
    prof = Professor.objects.filter(user=user).first()
    if prof:
        if getattr(course, "instructor_id", None) == prof.id:
            return True
        if getattr(course, "professor_id", None) == prof.id:
            return True

    # TA assigned to this course?  (your TA model: course = ManyToManyField(Course))
    if TeachingAssistant.objects.filter(user=user, course__id=course.id).exists():
        return True

    # Enrolled student?
    student = Student.objects.filter(user=user).first()
    if student and Enrollment.objects.filter(student_id=student.id, course_id=course.id).exists():
        return True

    return False
