import { listInterventions } from '@/lib/data/interventions';
import { loadExistingStudents } from '@/lib/data/students';
import InterventionForm from '@/components/intervention-form';
import InterventionTable from '@/components/intervention-table';

export default async function InterventionsPage() {
  const [rows, students] = await Promise.all([listInterventions(), loadExistingStudents()]);

  return (
    <section className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
      <InterventionForm
        students={students.map((student) => ({
          id: student.id,
          name: student.name,
          studentId: student.studentId
        }))}
      />
      <InterventionTable
        initialRows={rows.map((row) => ({
          intervention: {
            id: row.intervention.id,
            title: row.intervention.title,
            interventionType: row.intervention.interventionType,
            status: row.intervention.status,
            priority: row.intervention.priority,
            assignedTo: row.intervention.assignedTo,
            dueDate: row.intervention.dueDate ? row.intervention.dueDate.toISOString() : null
          },
          student: row.student
            ? { name: row.student.name, studentId: row.student.studentId }
            : null
        }))}
      />
    </section>
  );
}
