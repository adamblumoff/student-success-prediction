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
  seedStudentsForInstitution: (institutionId: number, students: StudentWithRisk[]) => void;
  loadInterventionsForInstitution: (institutionId?: number | null) => Promise<void>;
  loadInsightsForInstitution: (institutionId?: number | null) => Promise<void>;
  isLoadingInsights: boolean;
  isLoadingInterventions: boolean;
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
  const initialStudentsInstitutionId = initialStudents[0]?.institutionId ?? null;
  const initialInsightsInstitutionId = initialInsights[0]?.institutionId ?? null;
  const initialInterventionsInstitutionId = initialInterventions[0]?.institutionId ?? null;
  const derivedInitialInstitutionId =
    initialInstitutionId ??
    initialStudentsInstitutionId ??
    initialInterventionsInstitutionId ??
    initialInsightsInstitutionId ??
    institutions[0]?.id ??
    null;

  const [selectedInstitutionId, setSelectedInstitutionIdState] = useState<number | null>(
    derivedInitialInstitutionId
  );
  const [studentsByInstitution, setStudentsByInstitution] = useState<
    Record<number, StudentWithRisk[]>
  >(() =>
    derivedInitialInstitutionId ? { [derivedInitialInstitutionId]: initialStudents } : {}
  );
  const [insightsByInstitution, setInsightsByInstitution] = useState<
    Record<number, InsightPayload[]>
  >(() =>
    initialInsightsInstitutionId ? { [initialInsightsInstitutionId]: initialInsights } : {}
  );
  const [interventionsByInstitution, setInterventionsByInstitution] = useState<
    Record<number, InterventionPayload[]>
  >(() =>
    initialInterventionsInstitutionId
      ? { [initialInterventionsInstitutionId]: initialInterventions }
      : {}
  );
  const [isLoadingAll, setIsLoadingAll] = useState(false);
  const [loadingInterventionsFor, setLoadingInterventionsFor] = useState<number | null>(null);
  const [loadingInsightsFor, setLoadingInsightsFor] = useState<number | null>(null);

  useEffect(() => {
    const stored = readStoredInstitutionId();
    if (stored && stored !== selectedInstitutionId && institutions.some((item) => item.id === stored)) {
      setSelectedInstitutionIdState(stored);
      writeInstitutionCookie(stored);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!selectedInstitutionId) return;
    if (studentsByInstitution[selectedInstitutionId]) return;

    let cancelled = false;
    const loadInstitution = async () => {
      setIsLoadingAll(true);
      try {
        const response = await fetch(
          `/api/data/all?institutionId=${selectedInstitutionId}&includeStudents=1&includeInsights=0&includeInterventions=0`,
          { cache: 'no-store' }
        );
        if (!response.ok) return;
        const payload = (await response.json()) as {
          students: StudentWithRisk[];
          insights: InsightPayload[];
          interventions: InterventionPayload[];
        };
        if (cancelled) return;
        setStudentsByInstitution((prev) => ({
          ...prev,
          [selectedInstitutionId]: payload.students
        }));
      } catch {
        // Ignore background load failures; fallback to initial data.
      } finally {
        if (!cancelled) setIsLoadingAll(false);
      }
    };

    const timer = window.setTimeout(loadInstitution, 0);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [selectedInstitutionId, studentsByInstitution]);

  const setSelectedInstitutionId = useCallback((id: number) => {
    setSelectedInstitutionIdState(id);
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(STORAGE_KEY, String(id));
    }
    writeInstitutionCookie(id);
  }, []);

  const seedStudentsForInstitution = useCallback(
    (institutionId: number, nextStudents: StudentWithRisk[]) => {
      if (!institutionId) return;
      setStudentsByInstitution((prev) => ({
        ...prev,
        [institutionId]: nextStudents
      }));
    },
    []
  );

  const loadInterventionsForInstitution = useCallback(
    async (institutionId?: number | null) => {
      if (!institutionId) return;
      if (interventionsByInstitution[institutionId]) return;
      if (loadingInterventionsFor === institutionId) return;

      setLoadingInterventionsFor(institutionId);
      try {
        const response = await fetch(
          `/api/data/all?institutionId=${institutionId}&includeStudents=0&includeInsights=0&includeInterventions=1`,
          { cache: 'no-store' }
        );
        if (!response.ok) return;
        const payload = (await response.json()) as {
          interventions: InterventionPayload[];
        };
        setInterventionsByInstitution((prev) => ({
          ...prev,
          [institutionId]: payload.interventions
        }));
      } catch {
        // Ignore intervention load failures; fallback to empty state.
      } finally {
        setLoadingInterventionsFor((current) => (current === institutionId ? null : current));
      }
    },
    [interventionsByInstitution, loadingInterventionsFor]
  );

  const loadInsightsForInstitution = useCallback(
    async (institutionId?: number | null) => {
      if (!institutionId) return;
      if (insightsByInstitution[institutionId]) return;
      if (loadingInsightsFor === institutionId) return;

      setLoadingInsightsFor(institutionId);
      try {
        const response = await fetch(`/api/insights/latest?institutionId=${institutionId}`, {
          cache: 'no-store'
        });
        if (!response.ok) return;
        const payload = (await response.json()) as { insights: InsightPayload[] };
        setInsightsByInstitution((prev) => ({
          ...prev,
          [institutionId]: payload.insights
        }));
      } catch {
        // Ignore insight load failures; insights can still be generated on demand.
      } finally {
        setLoadingInsightsFor((current) => (current === institutionId ? null : current));
      }
    },
    [insightsByInstitution, loadingInsightsFor]
  );

  const students = useMemo(() => {
    if (!selectedInstitutionId) return initialStudents;
    return studentsByInstitution[selectedInstitutionId] ?? [];
  }, [initialStudents, selectedInstitutionId, studentsByInstitution]);

  const insights = useMemo(() => {
    if (!selectedInstitutionId) return initialInsights;
    return insightsByInstitution[selectedInstitutionId] ?? [];
  }, [initialInsights, insightsByInstitution, selectedInstitutionId]);

  const interventions = useMemo(() => {
    if (!selectedInstitutionId) return initialInterventions;
    return interventionsByInstitution[selectedInstitutionId] ?? [];
  }, [initialInterventions, interventionsByInstitution, selectedInstitutionId]);

  const value = useMemo(
    () => ({
      institutions,
      selectedInstitutionId,
      setSelectedInstitutionId,
      students,
      insights,
      interventions,
      seedStudentsForInstitution,
      loadInterventionsForInstitution,
      loadInsightsForInstitution,
      isLoadingInsights:
        selectedInstitutionId !== null && loadingInsightsFor === selectedInstitutionId,
      isLoadingInterventions:
        selectedInstitutionId !== null && loadingInterventionsFor === selectedInstitutionId,
      isLoadingAll
    }),
    [
      institutions,
      selectedInstitutionId,
      setSelectedInstitutionId,
      students,
      insights,
      interventions,
      seedStudentsForInstitution,
      loadInterventionsForInstitution,
      loadInsightsForInstitution,
      loadingInsightsFor,
      loadingInterventionsFor,
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
