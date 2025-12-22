'use client';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState
} from 'react';

export type InstitutionOption = {
  id: number;
  name: string;
};

export type StudentWithRisk = {
  id: number;
  institutionId: number;
  studentId: string;
  name: string | null;
  gradeLevel: string | null;
  currentGpa: number | null;
  attendanceRate: number | null;
  enrollmentStatus: string | null;
  assignedCounselor: string | null;
  lastActivity: string | null;
  activeInterventions: number | null;
  riskCategory: string | null;
  riskScore: number | null;
  confidenceScore: number | null;
  predictionDate: string | null;
};

export type InsightPayload = {
  studentDatabaseId: number;
  institutionId: number;
  formattedHtml: string | null;
  riskLevel: string | null;
  createdAt: string | null;
};

export type InterventionPayload = {
  id: number;
  studentId: number | null;
  institutionId: number;
  title: string;
  interventionType: string;
  status: string | null;
  priority: string | null;
  assignedTo: string | null;
  dueDate: string | null;
  createdAt: string | null;
  completedDate: string | null;
  studentName: string | null;
  studentIdentifier: string | null;
};

type AppDataContextValue = {
  institutions: InstitutionOption[];
  selectedInstitutionId: number | null;
  setSelectedInstitutionId: (id: number) => void;
  students: StudentWithRisk[];
  insights: InsightPayload[];
  interventions: InterventionPayload[];
  isLoadingAll: boolean;
};

const AppDataContext = createContext<AppDataContextValue | null>(null);

const STORAGE_KEY = 'activeInstitutionId';

const readStoredInstitutionId = () => {
  if (typeof window === 'undefined') return null;
  const stored = window.localStorage.getItem(STORAGE_KEY);
  const parsed = stored ? Number(stored) : NaN;
  return Number.isFinite(parsed) ? parsed : null;
};

const writeInstitutionCookie = (id: number) => {
  if (typeof document === 'undefined') return;
  document.cookie = `activeInstitutionId=${id}; path=/; samesite=lax; max-age=31536000`;
};

export default function AppDataProvider({
  children,
  institutions,
  initialInstitutionId,
  initialStudents,
  initialInsights,
  initialInterventions
}: {
  children: React.ReactNode;
  institutions: InstitutionOption[];
  initialInstitutionId: number | null;
  initialStudents: StudentWithRisk[];
  initialInsights: InsightPayload[];
  initialInterventions: InterventionPayload[];
}) {
  const [selectedInstitutionId, setSelectedInstitutionIdState] = useState<number | null>(
    initialInstitutionId ?? institutions[0]?.id ?? null
  );
  const [allStudents, setAllStudents] = useState<StudentWithRisk[] | null>(null);
  const [allInsights, setAllInsights] = useState<InsightPayload[] | null>(null);
  const [allInterventions, setAllInterventions] = useState<InterventionPayload[] | null>(null);
  const [isLoadingAll, setIsLoadingAll] = useState(false);

  useEffect(() => {
    const stored = readStoredInstitutionId();
    if (stored && stored !== selectedInstitutionId && institutions.some((item) => item.id === stored)) {
      setSelectedInstitutionIdState(stored);
      writeInstitutionCookie(stored);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    let cancelled = false;
    const loadAll = async () => {
      setIsLoadingAll(true);
      try {
        const response = await fetch('/api/data/all', { cache: 'no-store' });
        if (!response.ok) return;
        const payload = (await response.json()) as {
          students: StudentWithRisk[];
          insights: InsightPayload[];
          interventions: InterventionPayload[];
        };
        if (cancelled) return;
        setAllStudents(payload.students);
        setAllInsights(payload.insights);
        setAllInterventions(payload.interventions);
      } catch {
        // Ignore background load failures; fallback to initial data.
      } finally {
        if (!cancelled) setIsLoadingAll(false);
      }
    };

    const timer = window.setTimeout(loadAll, 0);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, []);

  const setSelectedInstitutionId = useCallback((id: number) => {
    setSelectedInstitutionIdState(id);
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(STORAGE_KEY, String(id));
    }
    writeInstitutionCookie(id);
  }, []);

  const students = useMemo(() => {
    const base = allStudents ?? initialStudents;
    if (!selectedInstitutionId) return base;
    return base.filter((student) => student.institutionId === selectedInstitutionId);
  }, [allStudents, initialStudents, selectedInstitutionId]);

  const insights = useMemo(() => {
    const base = allInsights ?? initialInsights;
    if (!selectedInstitutionId) return base;
    return base.filter((insight) => insight.institutionId === selectedInstitutionId);
  }, [allInsights, initialInsights, selectedInstitutionId]);

  const interventions = useMemo(() => {
    const base = allInterventions ?? initialInterventions;
    if (!selectedInstitutionId) return base;
    return base.filter((row) => row.institutionId === selectedInstitutionId);
  }, [allInterventions, initialInterventions, selectedInstitutionId]);

  const value = useMemo(
    () => ({
      institutions,
      selectedInstitutionId,
      setSelectedInstitutionId,
      students,
      insights,
      interventions,
      isLoadingAll
    }),
    [
      institutions,
      selectedInstitutionId,
      setSelectedInstitutionId,
      students,
      insights,
      interventions,
      isLoadingAll
    ]
  );

  return <AppDataContext.Provider value={value}>{children}</AppDataContext.Provider>;
}

export function useAppData() {
  const context = useContext(AppDataContext);
  if (!context) {
    throw new Error('useAppData must be used within AppDataProvider');
  }
  return context;
}
