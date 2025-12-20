import UploadForm from '@/components/upload-form';

export default function UploadPage() {
  return (
    <section className="space-y-6">
      <div>
        <p className="text-xs uppercase tracking-[0.35em] text-ink-400">Upload</p>
        <h1 className="mt-2 text-3xl font-semibold text-ink-50">Import a gradebook</h1>
        <p className="mt-2 text-sm text-ink-300">
          Analyze new student data and refresh the prediction engine in seconds.
        </p>
      </div>
      <UploadForm />
    </section>
  );
}
