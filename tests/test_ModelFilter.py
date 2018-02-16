

class TestModelFilter(object):

    def test_filter_by_id(self, Teacher):
        teacher_id = Teacher().save().id
        assert Teacher.filter({'id': teacher_id}).one().id == teacher_id

    def test_filter_by_one_to_many_relationship(self, Teacher, Student):
        student = Student(name='foo')
        teacher_id = Teacher(students=[student]).save().id
        assert Teacher.filter({
            'students.name': student.name
        }).one().id == teacher_id

    def test_filter_by_one_to_one_relationship(self, Classroom, Teacher):
        teacher = Teacher()
        classroom_id = Classroom(teacher=teacher).save().id
        assert Classroom.filter({
            'teacher.id': teacher.id
        }).one().id == classroom_id

    def test_filter_by_foreign_key(self, Classroom, Teacher):
        teacher = Teacher()
        classroom_id = Classroom(teacher=teacher).save().id
        assert Classroom.filter({
            'teacher_id': teacher.id
        }).one().id == classroom_id
