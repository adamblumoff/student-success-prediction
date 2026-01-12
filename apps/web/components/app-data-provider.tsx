'use client';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState
} from 'react';
import { useAuth } from '@clerk/nextjs';
import type { RealtimeEvent } from '@/lib/realtime';

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

export type DashboardStats = {
  totalStudents: number;
  totalPredictions: number;
  totalInterventions: number;
  riskDistribution: {
    high: number;
    medium: number;
    low: number;
    unknown: number;
  };
  latestPredictionDate: string | null;
  recentPredictions: number;
  previousPredictions: number;
  recentInterventions: number;
  completedInterventions: number;
  topRiskStudents: Array<{
    id: number;
    name: string | null;
    studentId: string;
    gradeLevel: string | null;
    riskScore: number;
    riskCategory: string | null;
    confidenceScore: number | null;
  }>;
};

export type DashboardStatsPayload = DashboardStats & {
  version: string | null;
};

type VersionMap = Record<number, string>;
type StaleMap = Record<number, boolean>;

type AppDataContextValue = {
  institutions: InstitutionOption[];
  selectedInstitutionId: number | null;
  setSelectedInstitutionId: (id: number) => void;
  students: StudentWithRisk[];
  insights: InsightPayload[];
  interventions: InterventionPayload[];
  seedStudentsForInstitution: (
    institutionId: number,
    students: StudentWithRisk[],
    version?: string | null
  ) => void;
  seedInsightsForInstitution: (
    institutionId: number,
    insights: InsightPayload[],
    version?: string | null
  ) => void;
  seedInterventionsForInstitution: (
    institutionId: number,
    interventions: InterventionPayload[],
    version?: string | null
  ) => void;
  loadInterventionsForInstitution: (institutionId?: number | null) => Promise<void>;
  loadInsightsForInstitution: (
    institutionId?: number | null,
    options?: { force?: boolean }
  ) => Promise<void>;
  studentsVersionByInstitution: VersionMap;
  insightsVersionByInstitution: VersionMap;
  interventionsVersionByInstitution: VersionMap;
  studentsStaleByInstitution: StaleMap;
  insightsStaleByInstitution: StaleMap;
  interventionsStaleByInstitution: StaleMap;
  dashboardStatsByInstitution: Record<number, DashboardStats>;
  dashboardStatsVersionByInstitution: VersionMap;
  dashboardStatsStaleByInstitution: StaleMap;
  setDashboardStatsForInstitution: (
    institutionId: number,
    stats: DashboardStats,
    version: string | null
  ) => void;
  markDashboardStatsStale: (institutionId?: number | null | 'all') => void;
  markStudentsStale: (institutionId?: number | null | 'all') => void;
  markInsightsStale: (institutionId?: number | null | 'all') => void;
  markInterventionsStale: (institutionId?: number | null | 'all') => void;
  isLoadingInsights: boolean;
  isLoadingInterventions: boolean;
  isLoadingAll: boolean;
};

const AppDataContext = createContext<AppDataContextValue | null>(null);

const STORAGE_KEY = 'activeInstitutionId';
const CACHE_SCHEMA_VERSION = 1;

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

type PersistedCache = {
  schemaVersion: number;
  updatedAt: string;
  studentsByInstitution: Record<number, StudentWithRisk[]>;
  insightsByInstitution: Record<number, InsightPayload[]>;
  interventionsByInstitution: Record<number, InterventionPayload[]>;
  dashboardStatsByInstitution: Record<number, DashboardStats>;
  studentsVersionByInstitution: VersionMap;
  insightsVersionByInstitution: VersionMap;
  interventionsVersionByInstitution: VersionMap;
  dashboardStatsVersionByInstitution: VersionMap;
  studentsStaleByInstitution: StaleMap;
  insightsStaleByInstitution: StaleMap;
  interventionsStaleByInstitution: StaleMap;
  dashboardStatsStaleByInstitution: StaleMap;
};

const parsePersistedCache = (raw: string | null): PersistedCache | null => {
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as PersistedCache;
    if (parsed.schemaVersion !== CACHE_SCHEMA_VERSION) return null;
    return parsed;
  } catch {
    return null;
  }
};

const clearUserCache = (id: string) => {
  if (typeof window === 'undefined') return;
  const prefix = `ss-cache:${id}:`;
  for (let index = window.localStorage.length - 1; index >= 0; index -= 1) {
    const key = window.localStorage.key(index);
    if (key && key.startsWith(prefix)) {
      window.localStorage.removeItem(key);
    }
  }
};

export default function AppDataProvider({
  children,
  institutions,
  districtId,
  initialInstitutionId,
  initialStudents,
  initialInsights,
  initialInterventions
}: {
  children: React.ReactNode;
  institutions: InstitutionOption[];
  districtId: number | null;
  initialInstitutionId: number | null;
  initialStudents: StudentWithRisk[];
  initialInsights: InsightPayload[];
  initialInterventions: InterventionPayload[];
}) {
  const { userId } = useAuth();
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
  const [studentsVersionByInstitution, setStudentsVersionByInstitution] =
    useState<VersionMap>({});
  const [insightsVersionByInstitution, setInsightsVersionByInstitution] =
    useState<VersionMap>({});
  const [interventionsVersionByInstitution, setInterventionsVersionByInstitution] =
    useState<VersionMap>({});
  const [studentsStaleByInstitution, setStudentsStaleByInstitution] = useState<StaleMap>({});
  const [insightsStaleByInstitution, setInsightsStaleByInstitution] = useState<StaleMap>({});
  const [interventionsStaleByInstitution, setInterventionsStaleByInstitution] =
    useState<StaleMap>({});
  const [dashboardStatsByInstitution, setDashboardStatsByInstitution] = useState<
    Record<number, DashboardStats>
  >({});
  const [dashboardStatsVersionByInstitution, setDashboardStatsVersionByInstitution] =
    useState<VersionMap>({});
  const [dashboardStatsStaleByInstitution, setDashboardStatsStaleByInstitution] =
    useState<StaleMap>({});
  const [isLoadingAll, setIsLoadingAll] = useState(false);
  const [loadingInterventionsFor, setLoadingInterventionsFor] = useState<number | null>(null);
  const [loadingInsightsFor, setLoadingInsightsFor] = useState<number | null>(null);
  const [cacheHydrated, setCacheHydrated] = useState(false);
  const insightsByInstitutionRef = useRef(insightsByInstitution);
  const loadingInsightsForRef = useRef(loadingInsightsFor);
  const insightsStaleByInstitutionRef = useRef(insightsStaleByInstitution);
  const storageKey = useMemo(
    () => (userId && districtId ? `ss-cache:${userId}:${districtId}` : null),
    [districtId, userId]
  );
  const previousUserIdRef = useRef<string | null>(null);

  useEffect(() => {
    insightsByInstitutionRef.current = insightsByInstitution;
  }, [insightsByInstitution]);

  useEffect(() => {
    loadingInsightsForRef.current = loadingInsightsFor;
  }, [loadingInsightsFor]);

  useEffect(() => {
    insightsStaleByInstitutionRef.current = insightsStaleByInstitution;
  }, [insightsStaleByInstitution]);

  useEffect(() => {
    const stored = readStoredInstitutionId();
    if (stored && stored !== selectedInstitutionId && institutions.some((item) => item.id === stored)) {
      setSelectedInstitutionIdState(stored);
      writeInstitutionCookie(stored);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const previousUserId = previousUserIdRef.current;
    if (previousUserId && userId !== previousUserId) {
      clearUserCache(previousUserId);
      setStudentsByInstitution({});
      setInsightsByInstitution({});
      setInterventionsByInstitution({});
      setDashboardStatsByInstitution({});
      setStudentsVersionByInstitution({});
      setInsightsVersionByInstitution({});
      setInterventionsVersionByInstitution({});
      setDashboardStatsVersionByInstitution({});
      setStudentsStaleByInstitution({});
      setInsightsStaleByInstitution({});
      setInterventionsStaleByInstitution({});
      setDashboardStatsStaleByInstitution({});
    }
    previousUserIdRef.current = userId ?? null;
  }, [userId]);

  useEffect(() => {
    if (!storageKey) return;
    if (typeof window === 'undefined') return;
    setCacheHydrated(false);
    const stored = parsePersistedCache(window.localStorage.getItem(storageKey));
    if (stored) {
      setStudentsByInstitution((prev) => ({ ...stored.studentsByInstitution, ...prev }));
      setInsightsByInstitution((prev) => ({ ...stored.insightsByInstitution, ...prev }));
      setInterventionsByInstitution((prev) => ({ ...stored.interventionsByInstitution, ...prev }));
      setDashboardStatsByInstitution((prev) => ({
        ...stored.dashboardStatsByInstitution,
        ...prev
      }));
      setStudentsVersionByInstitution((prev) => ({
        ...stored.studentsVersionByInstitution,
        ...prev
      }));
      setInsightsVersionByInstitution((prev) => ({
        ...stored.insightsVersionByInstitution,
        ...prev
      }));
      setInterventionsVersionByInstitution((prev) => ({
        ...stored.interventionsVersionByInstitution,
        ...prev
      }));
      setDashboardStatsVersionByInstitution((prev) => ({
        ...stored.dashboardStatsVersionByInstitution,
        ...prev
      }));
      setStudentsStaleByInstitution((prev) => ({
        ...stored.studentsStaleByInstitution,
        ...prev
      }));
      setInsightsStaleByInstitution((prev) => ({
        ...stored.insightsStaleByInstitution,
        ...prev
      }));
      setInterventionsStaleByInstitution((prev) => ({
        ...stored.interventionsStaleByInstitution,
        ...prev
      }));
      setDashboardStatsStaleByInstitution((prev) => ({
        ...stored.dashboardStatsStaleByInstitution,
        ...prev
      }));
    }
    setCacheHydrated(true);
  }, [storageKey]);

  useEffect(() => {
    if (!storageKey) return;
    if (typeof window === 'undefined') return;
    if (!cacheHydrated) return;
    const payload: PersistedCache = {
      schemaVersion: CACHE_SCHEMA_VERSION,
      updatedAt: new Date().toISOString(),
      studentsByInstitution,
      insightsByInstitution,
      interventionsByInstitution,
      dashboardStatsByInstitution,
      studentsVersionByInstitution,
      insightsVersionByInstitution,
      interventionsVersionByInstitution,
      dashboardStatsVersionByInstitution,
      studentsStaleByInstitution,
      insightsStaleByInstitution,
      interventionsStaleByInstitution,
      dashboardStatsStaleByInstitution
    };
    window.localStorage.setItem(storageKey, JSON.stringify(payload));
  }, [
    storageKey,
    cacheHydrated,
    studentsByInstitution,
    insightsByInstitution,
    interventionsByInstitution,
    dashboardStatsByInstitution,
    studentsVersionByInstitution,
    insightsVersionByInstitution,
    interventionsVersionByInstitution,
    dashboardStatsVersionByInstitution,
    studentsStaleByInstitution,
    insightsStaleByInstitution,
    interventionsStaleByInstitution,
    dashboardStatsStaleByInstitution
  ]);

  useEffect(() => {
    if (!storageKey) return;
    if (typeof window === 'undefined') return;
    const handleStorage = (event: StorageEvent) => {
      if (event.key !== storageKey) return;
      const stored = parsePersistedCache(event.newValue);
      if (!stored) return;
      setStudentsByInstitution(stored.studentsByInstitution);
      setInsightsByInstitution(stored.insightsByInstitution);
      setInterventionsByInstitution(stored.interventionsByInstitution);
      setDashboardStatsByInstitution(stored.dashboardStatsByInstitution);
      setStudentsVersionByInstitution(stored.studentsVersionByInstitution);
      setInsightsVersionByInstitution(stored.insightsVersionByInstitution);
      setInterventionsVersionByInstitution(stored.interventionsVersionByInstitution);
      setDashboardStatsVersionByInstitution(stored.dashboardStatsVersionByInstitution);
      setStudentsStaleByInstitution(stored.studentsStaleByInstitution);
      setInsightsStaleByInstitution(stored.insightsStaleByInstitution);
      setInterventionsStaleByInstitution(stored.interventionsStaleByInstitution);
      setDashboardStatsStaleByInstitution(stored.dashboardStatsStaleByInstitution);
    };
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, [storageKey]);

  useEffect(() => {
    if (!selectedInstitutionId) return;
    const cached = studentsByInstitution[selectedInstitutionId];
    const isStale = studentsStaleByInstitution[selectedInstitutionId];
    if (cached && !isStale) return;

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
          studentsVersion?: string | null;
        };
        if (cancelled) return;
        setStudentsByInstitution((prev) => ({
          ...prev,
          [selectedInstitutionId]: payload.students
        }));
        if (payload.studentsVersion) {
          setStudentsVersionByInstitution((prev) => ({
            ...prev,
            [selectedInstitutionId]: payload.studentsVersion ?? ''
          }));
        }
        setStudentsStaleByInstitution((prev) => ({
          ...prev,
          [selectedInstitutionId]: false
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
  }, [selectedInstitutionId, studentsByInstitution, studentsStaleByInstitution]);

  const setSelectedInstitutionId = useCallback((id: number) => {
    setSelectedInstitutionIdState(id);
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(STORAGE_KEY, String(id));
    }
    writeInstitutionCookie(id);
  }, []);

  const seedStudentsForInstitution = useCallback(
    (institutionId: number, nextStudents: StudentWithRisk[], version?: string | null) => {
      if (!institutionId) return;
      setStudentsByInstitution((prev) => ({
        ...prev,
        [institutionId]: nextStudents
      }));
      if (version) {
        setStudentsVersionByInstitution((prev) => ({
          ...prev,
          [institutionId]: version
        }));
      }
      setStudentsStaleByInstitution((prev) => ({
        ...prev,
        [institutionId]: false
      }));
    },
    []
  );

  const seedInsightsForInstitution = useCallback(
    (institutionId: number, nextInsights: InsightPayload[], version?: string | null) => {
      if (!institutionId) return;
      setInsightsByInstitution((prev) => ({
        ...prev,
        [institutionId]: nextInsights
      }));
      if (version) {
        setInsightsVersionByInstitution((prev) => ({
          ...prev,
          [institutionId]: version
        }));
      }
      setInsightsStaleByInstitution((prev) => ({
        ...prev,
        [institutionId]: false
      }));
    },
    []
  );

  const seedInterventionsForInstitution = useCallback(
    (institutionId: number, nextInterventions: InterventionPayload[], version?: string | null) => {
      if (!institutionId) return;
      setInterventionsByInstitution((prev) => ({
        ...prev,
        [institutionId]: nextInterventions
      }));
      if (version) {
        setInterventionsVersionByInstitution((prev) => ({
          ...prev,
          [institutionId]: version
        }));
      }
      setInterventionsStaleByInstitution((prev) => ({
        ...prev,
        [institutionId]: false
      }));
    },
    []
  );

  const setDashboardStatsForInstitution = useCallback(
    (institutionId: number, stats: DashboardStats, version: string | null) => {
      if (!institutionId) return;
      setDashboardStatsByInstitution((prev) => ({
        ...prev,
        [institutionId]: stats
      }));
      if (version) {
        setDashboardStatsVersionByInstitution((prev) => ({
          ...prev,
          [institutionId]: version
        }));
      }
      setDashboardStatsStaleByInstitution((prev) => ({
        ...prev,
        [institutionId]: false
      }));
    },
    []
  );

  const markDashboardStatsStale = useCallback(
    (institutionId?: number | null | 'all') => {
      if (!institutionId || institutionId === 'all') {
        setDashboardStatsStaleByInstitution((prev) => {
          const next: Record<number, boolean> = { ...prev };
          for (const item of institutions) {
            next[item.id] = true;
          }
          return next;
        });
        return;
      }
      setDashboardStatsStaleByInstitution((prev) => ({
        ...prev,
        [institutionId]: true
      }));
    },
    [institutions]
  );

  const markStudentsStale = useCallback(
    (institutionId?: number | null | 'all') => {
      if (!institutionId || institutionId === 'all') {
        setStudentsStaleByInstitution((prev) => {
          const next: StaleMap = { ...prev };
          for (const item of institutions) {
            next[item.id] = true;
          }
          return next;
        });
        return;
      }
      setStudentsStaleByInstitution((prev) => ({
        ...prev,
        [institutionId]: true
      }));
    },
    [institutions]
  );

  const markInsightsStale = useCallback(
    (institutionId?: number | null | 'all') => {
      if (!institutionId || institutionId === 'all') {
        setInsightsStaleByInstitution((prev) => {
          const next: StaleMap = { ...prev };
          for (const item of institutions) {
            next[item.id] = true;
          }
          return next;
        });
        return;
      }
      setInsightsStaleByInstitution((prev) => ({
        ...prev,
        [institutionId]: true
      }));
    },
    [institutions]
  );

  const markInterventionsStale = useCallback(
    (institutionId?: number | null | 'all') => {
      if (!institutionId || institutionId === 'all') {
        setInterventionsStaleByInstitution((prev) => {
          const next: StaleMap = { ...prev };
          for (const item of institutions) {
            next[item.id] = true;
          }
          return next;
        });
        return;
      }
      setInterventionsStaleByInstitution((prev) => ({
        ...prev,
        [institutionId]: true
      }));
    },
    [institutions]
  );

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const handler = (event: Event) => {
      const detail = (event as CustomEvent<RealtimeEvent>).detail;
      if (!detail || detail.type !== 'data:mutation') return;
      const paths = detail.paths ?? [];
      const target = detail.institutionId ?? 'all';
      if (paths.length === 0) {
        markDashboardStatsStale('all');
        markStudentsStale('all');
        markInsightsStale('all');
        markInterventionsStale('all');
        return;
      }
      if (paths.includes('/dashboard')) markDashboardStatsStale(target);
      if (paths.includes('/students')) markStudentsStale(target);
      if (paths.includes('/insights')) markInsightsStale(target);
      if (paths.includes('/interventions')) markInterventionsStale(target);
    };
    window.addEventListener('data:mutation', handler as EventListener);
    return () => window.removeEventListener('data:mutation', handler as EventListener);
  }, [markDashboardStatsStale, markInterventionsStale, markInsightsStale, markStudentsStale]);

  const loadInterventionsForInstitution = useCallback(
    async (institutionId?: number | null) => {
      if (!institutionId) return;
      const cached = interventionsByInstitution[institutionId];
      const isStale = interventionsStaleByInstitution[institutionId];
      if (cached && !isStale) return;
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
          interventionsVersion?: string | null;
        };
        setInterventionsByInstitution((prev) => ({
          ...prev,
          [institutionId]: payload.interventions
        }));
        if (payload.interventionsVersion) {
          setInterventionsVersionByInstitution((prev) => ({
            ...prev,
            [institutionId]: payload.interventionsVersion ?? ''
          }));
        }
        setInterventionsStaleByInstitution((prev) => ({
          ...prev,
          [institutionId]: false
        }));
      } catch {
        // Ignore intervention load failures; fallback to empty state.
      } finally {
        setLoadingInterventionsFor((current) => (current === institutionId ? null : current));
      }
    },
    [interventionsByInstitution, interventionsStaleByInstitution, loadingInterventionsFor]
  );

  const loadInsightsForInstitution = useCallback(
    async (institutionId?: number | null, options?: { force?: boolean }) => {
      if (!institutionId) return;
      const cached = insightsByInstitutionRef.current[institutionId];
      const isStale = insightsStaleByInstitutionRef.current[institutionId];
      if (!options?.force && cached && !isStale) return;
      if (loadingInsightsForRef.current === institutionId) return;

      setLoadingInsightsFor(institutionId);
      try {
        const response = await fetch(`/api/insights/latest?institutionId=${institutionId}`, {
          cache: 'no-store'
        });
        if (!response.ok) return;
        const payload = (await response.json()) as {
          insights: InsightPayload[];
          version?: string | null;
        };
        setInsightsByInstitution((prev) => ({
          ...prev,
          [institutionId]: payload.insights
        }));
        if (payload.version) {
          setInsightsVersionByInstitution((prev) => ({
            ...prev,
            [institutionId]: payload.version ?? ''
          }));
        }
        setInsightsStaleByInstitution((prev) => ({
          ...prev,
          [institutionId]: false
        }));
      } catch {
        // Ignore insight load failures; insights can still be generated on demand.
      } finally {
        setLoadingInsightsFor((current) => (current === institutionId ? null : current));
      }
    },
    []
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
      seedInsightsForInstitution,
      seedInterventionsForInstitution,
      loadInterventionsForInstitution,
      loadInsightsForInstitution,
      studentsVersionByInstitution,
      insightsVersionByInstitution,
      interventionsVersionByInstitution,
      studentsStaleByInstitution,
      insightsStaleByInstitution,
      interventionsStaleByInstitution,
      dashboardStatsByInstitution,
      dashboardStatsVersionByInstitution,
      dashboardStatsStaleByInstitution,
      setDashboardStatsForInstitution,
      markDashboardStatsStale,
      markStudentsStale,
      markInsightsStale,
      markInterventionsStale,
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
      seedInsightsForInstitution,
      seedInterventionsForInstitution,
      loadInterventionsForInstitution,
      loadInsightsForInstitution,
      studentsVersionByInstitution,
      insightsVersionByInstitution,
      interventionsVersionByInstitution,
      studentsStaleByInstitution,
      insightsStaleByInstitution,
      interventionsStaleByInstitution,
      dashboardStatsByInstitution,
      dashboardStatsVersionByInstitution,
      dashboardStatsStaleByInstitution,
      setDashboardStatsForInstitution,
      markDashboardStatsStale,
      markStudentsStale,
      markInsightsStale,
      markInterventionsStale,
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
