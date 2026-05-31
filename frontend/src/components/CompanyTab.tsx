import React, { useState, useEffect, useRef } from 'react';
import { 
  Briefcase, 
  Play, 
  Square, 
  RotateCw, 
  Edit, 
  Trash2, 
  Plus, 
  FileText, 
  Image as ImageIcon, 
  File, 
  CheckCircle2, 
  XCircle, 
  AlertCircle, 
  ChevronDown, 
  ChevronUp, 
  Download, 
  Send,
  HelpCircle,
  Eye,
  Code,
  Sparkles
} from 'lucide-react';
import { api, TaskState, ExecutionPlan, PlanStep, Artifact, StepResult, StepError } from '../api';

export default function CompanyTab() {
  const [tasks, setTasks] = useState<TaskState[]>([]);
  const [activeTask, setActiveTask] = useState<TaskState | null>(null);
  const [query, setQuery] = useState('');
  const [isLoadingTasks, setIsLoadingTasks] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [editingPlan, setEditingPlan] = useState<ExecutionPlan | null>(null);
  const [showRawJson, setShowRawJson] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  // Load all tasks on mount
  useEffect(() => {
    loadTasks();
    return () => stopPolling();
  }, []);

  // Poll active task status if it's currently executing or planning
  useEffect(() => {
    if (activeTask && (activeTask.status === 'executing' || activeTask.status === 'planning')) {
      startPolling(activeTask.task_id);
    } else {
      stopPolling();
    }
  }, [activeTask?.status, activeTask?.task_id]);

  const loadTasks = async () => {
    setIsLoadingTasks(true);
    const res = await api.listTasks();
    if (res.success && res.data) {
      setTasks(res.data);
    } else {
      setErrorMsg(res.error || 'Failed to retrieve task history.');
    }
    setIsLoadingTasks(false);
  };

  const startPolling = (taskId: string) => {
    stopPolling();
    pollingRef.current = setInterval(async () => {
      const res = await api.getTask(taskId);
      if (res.success && res.data) {
        setActiveTask(res.data);
        // Update task list item as well
        setTasks(prev => prev.map(t => t.task_id === taskId ? res.data! : t));
        
        // Stop polling if done
        const status = res.data.status;
        if (status !== 'executing' && status !== 'planning') {
          stopPolling();
        }
      }
    }, 2000);
  };

  const stopPolling = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  };

  const handleSelectTask = async (taskId: string) => {
    setErrorMsg(null);
    const res = await api.getTask(taskId);
    if (res.success && res.data) {
      setActiveTask(res.data);
      setEditingPlan(res.data.plan || null);
    } else {
      setErrorMsg(res.error || 'Failed to fetch task details.');
    }
  };

  const handleCreateTask = async () => {
    if (!query.trim()) return;
    setIsSubmitting(true);
    setErrorMsg(null);
    setActiveTask(null);
    setEditingPlan(null);

    const res = await api.createTask(query);
    if (res.success && res.data) {
      setQuery('');
      setActiveTask(res.data);
      setEditingPlan(res.data.plan || null);
      await loadTasks();
    } else {
      setErrorMsg(res.error || 'Supervisor failed to formulate a plan.');
    }
    setIsSubmitting(false);
  };

  const handleSavePlan = async () => {
    if (!activeTask || !editingPlan) return;
    setErrorMsg(null);
    const res = await api.updatePlan(activeTask.task_id, editingPlan);
    if (res.success && res.data) {
      setActiveTask(res.data);
      setEditingPlan(res.data.plan || null);
      await loadTasks();
    } else {
      setErrorMsg(res.error || 'Failed to save modifications to execution plan.');
    }
  };

  const handleConfirmTask = async () => {
    if (!activeTask) return;
    setErrorMsg(null);
    const res = await api.confirmTask(activeTask.task_id);
    if (res.success && res.data) {
      setActiveTask(res.data);
      await loadTasks();
    } else {
      setErrorMsg(res.error || 'Could not verify and execute the plan.');
    }
  };

  const handleCancelTask = async () => {
    if (!activeTask) return;
    setErrorMsg(null);
    const res = await api.cancelTask(activeTask.task_id);
    if (res.success && res.data) {
      setActiveTask(res.data);
      await loadTasks();
    } else {
      setErrorMsg(res.error || 'Failed to cancel executing task.');
    }
  };

  const handleRetryStep = async (stepId: string) => {
    if (!activeTask) return;
    setErrorMsg(null);
    const res = await api.retryStep(activeTask.task_id, stepId);
    if (res.success && res.data) {
      setActiveTask(res.data);
      setEditingPlan(res.data.plan || null);
      await loadTasks();
    } else {
      setErrorMsg(res.error || `Failed to restart step ${stepId}`);
    }
  };

  // Edit Step Helpers
  const handleEditStepField = (index: number, field: keyof PlanStep, value: any) => {
    if (!editingPlan) return;
    const steps = [...editingPlan.steps];
    steps[index] = { ...steps[index], [field]: value };
    setEditingPlan({ ...editingPlan, steps });
  };

  const handleEditInputRef = (stepIndex: number, key: string, val: string) => {
    if (!editingPlan) return;
    const steps = [...editingPlan.steps];
    const inputRefs = { ...steps[stepIndex].input_refs, [key]: val };
    steps[stepIndex] = { ...steps[stepIndex], input_refs: inputRefs };
    setEditingPlan({ ...editingPlan, steps });
  };

  const handleRemoveInputRef = (stepIndex: number, key: string) => {
    if (!editingPlan) return;
    const steps = [...editingPlan.steps];
    const inputRefs = { ...steps[stepIndex].input_refs };
    delete inputRefs[key];
    steps[stepIndex] = { ...steps[stepIndex], input_refs: inputRefs };
    setEditingPlan({ ...editingPlan, steps });
  };

  const handleAddInputRef = (stepIndex: number, key: string) => {
    if (!editingPlan || !key.trim()) return;
    const steps = [...editingPlan.steps];
    const inputRefs = { ...steps[stepIndex].input_refs, [key.trim()]: '' };
    steps[stepIndex] = { ...steps[stepIndex], input_refs: inputRefs };
    setEditingPlan({ ...editingPlan, steps });
  };

  const handleAddStep = () => {
    if (!editingPlan) return;
    const newStepId = `step_${editingPlan.steps.length + 1}`;
    const newStep: PlanStep = {
      step_id: newStepId,
      title: 'New Step',
      worker_name: 'text_worker',
      instruction: '',
      depends_on: [],
      input_refs: {},
      output_type: 'text',
      status: 'pending'
    };
    setEditingPlan({
      ...editingPlan,
      steps: [...editingPlan.steps, newStep]
    });
  };

  const handleDeleteStep = (index: number) => {
    if (!editingPlan) return;
    const steps = editingPlan.steps.filter((_, idx) => idx !== index);
    setEditingPlan({ ...editingPlan, steps });
  };

  const getStatusBadge = (status: string) => {
    const base = "px-2 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider ";
    switch (status) {
      case 'completed': return base + "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30";
      case 'executing': return base + "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 animate-pulse";
      case 'planning': return base + "bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 animate-pulse";
      case 'pending_approval': return base + "bg-purple-500/20 text-purple-400 border border-purple-500/30";
      case 'failed': return base + "bg-rose-500/20 text-rose-400 border border-rose-500/30";
      case 'planning_failed': return base + "bg-red-500/20 text-red-400 border border-red-500/30";
      case 'cancelled': return base + "bg-amber-500/20 text-amber-400 border border-amber-500/30";
      default: return base + "bg-zinc-500/20 text-zinc-400 border border-zinc-500/30";
    }
  };

  return (
    <div className="flex h-full w-full gap-4 p-4 text-zinc-200 overflow-hidden font-sans">
      {/* Task List / Sidebar */}
      <div className="w-80 flex flex-col gap-3 glass-panel p-4 border border-zinc-800/80 rounded-xl overflow-hidden shrink-0 bg-[#0c0914]/80 backdrop-blur-md">
        <div className="flex items-center gap-2 border-b border-zinc-800 pb-3">
          <Briefcase className="text-cyan-400" size={20} />
          <h2 className="text-lg font-bold text-zinc-100">Consulting Projects</h2>
        </div>

        {/* History List */}
        <div className="flex-1 overflow-y-auto space-y-2 pr-1">
          {isLoadingTasks ? (
            <div className="flex flex-col items-center justify-center h-32 gap-2 text-zinc-500">
              <RotateCw className="animate-spin text-cyan-400" size={24} />
              <span>Loading Projects...</span>
            </div>
          ) : tasks.length === 0 ? (
            <div className="text-zinc-600 text-sm text-center py-8">
              No consulting projects created yet.
            </div>
          ) : (
            tasks.map(t => {
              const isActive = activeTask?.task_id === t.task_id;
              const dateStr = new Date(t.created_at).toLocaleDateString(undefined, {
                month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
              });
              return (
                <button
                  key={t.task_id}
                  onClick={() => handleSelectTask(t.task_id)}
                  className={`w-full text-left p-3 rounded-lg border transition-all duration-200 ${
                    isActive 
                      ? 'bg-zinc-800/50 border-cyan-500/50 shadow-md shadow-cyan-950/20' 
                      : 'bg-zinc-900/30 border-zinc-800/60 hover:bg-zinc-800/20'
                  }`}
                >
                  <div className="flex justify-between items-start gap-1 mb-1">
                    <span className="font-semibold text-sm truncate text-zinc-200" title={t.plan?.title || t.user_query}>
                      {t.plan?.title || "Draft Project"}
                    </span>
                    <span className="shrink-0 text-[10px] text-zinc-500 mt-0.5">{dateStr}</span>
                  </div>
                  <p className="text-xs text-zinc-500 truncate mb-2">{t.user_query}</p>
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] text-zinc-600 font-mono">#{t.task_id.substring(5, 13)}</span>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                      t.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400' :
                      t.status === 'executing' ? 'bg-cyan-500/10 text-cyan-400 animate-pulse' :
                      t.status === 'failed' ? 'bg-rose-500/10 text-rose-400' : 'bg-zinc-800 text-zinc-400'
                    }`}>{t.status}</span>
                  </div>
                </button>
              );
            })
          )}
        </div>

        {/* Start New Project */}
        <div className="border-t border-zinc-800 pt-3">
          <button 
            onClick={() => { setActiveTask(null); setEditingPlan(null); setErrorMsg(null); }}
            className="w-full py-2 bg-gradient-to-r from-cyan-600 to-purple-600 hover:from-cyan-500 hover:to-purple-500 text-white rounded-lg text-sm font-semibold transition-all duration-300 shadow-lg shadow-purple-950/20 flex items-center justify-center gap-1.5"
          >
            <Plus size={16} />
            <span>Create New Draft</span>
          </button>
        </div>
      </div>

      {/* Main Workspace Area */}
      <div className="flex-1 flex flex-col gap-4 overflow-y-auto glass-panel p-5 border border-zinc-800/80 rounded-xl bg-[#0c0914]/40 backdrop-blur-md">
        
        {/* Error banner */}
        {errorMsg && (
          <div className="bg-rose-950/40 border border-rose-800/50 text-rose-300 p-3 rounded-lg flex items-center gap-3 text-sm">
            <AlertCircle className="text-rose-400 shrink-0" size={18} />
            <div className="flex-1">{errorMsg}</div>
            <button onClick={() => setErrorMsg(null)} className="text-rose-400 hover:text-rose-200 font-bold px-1">&times;</button>
          </div>
        )}

        {/* Input Prompt (If no active task or creating new) */}
        {!activeTask && (
          <div className="flex-1 flex flex-col items-center justify-center max-w-xl mx-auto text-center gap-6 py-12">
            <div className="p-4 bg-gradient-to-br from-cyan-500/15 to-purple-500/15 rounded-full border border-purple-500/20 shadow-inner">
              <Briefcase className="text-purple-400" size={48} />
            </div>
            <div>
              <h1 className="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-400 mb-2">
                Multi-Agent Consulting Agency
              </h1>
              <p className="text-zinc-400 text-sm leading-relaxed">
                Describe your business idea, marketing request, or consulting target. The AI Supervisor will formulate a multi-stage plan and assign specialized worker agents (text generation, graphic logos, and image editing) to deliver your finished package.
              </p>
            </div>

            <div className="w-full relative">
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g. Create a marketing slogan for 'CyberPie Cafe', design an neon-style futuristic pie logo, and edit it to include a glow effect on the crust..."
                rows={4}
                className="w-full bg-[#120e24]/90 border border-zinc-800 rounded-xl p-4 pr-12 text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-cyan-500 transition-colors resize-none shadow-lg"
              />
              <button
                disabled={isSubmitting || !query.trim()}
                onClick={handleCreateTask}
                className="absolute right-3 bottom-4 p-2 bg-cyan-600 hover:bg-cyan-500 disabled:bg-zinc-800 disabled:text-zinc-600 text-white rounded-lg transition-all"
              >
                {isSubmitting ? <RotateCw className="animate-spin" size={16} /> : <Send size={16} />}
              </button>
            </div>
          </div>
        )}

        {/* Active Task Workspace */}
        {activeTask && (
          <div className="space-y-5">
            {/* Header info */}
            <div className="flex flex-wrap justify-between items-center gap-3 border-b border-zinc-800 pb-4">
              <div>
                <div className="flex items-center gap-3">
                  <h1 className="text-xl font-bold text-zinc-100">
                    {activeTask.plan?.title || "Consulting Draft"}
                  </h1>
                  {getStatusBadge(activeTask.status)}
                </div>
                <div className="text-xs text-zinc-500 mt-1 flex items-center gap-2">
                  <span>Task ID: <code className="font-mono text-zinc-400">{activeTask.task_id}</code></span>
                  <span>&bull;</span>
                  <span>Created: {new Date(activeTask.created_at).toLocaleString()}</span>
                </div>
              </div>

              {/* Execution Actions */}
              <div className="flex gap-2">
                {activeTask.status === 'pending_approval' && (
                  <>
                    <button
                      onClick={handleSavePlan}
                      className="px-3 py-1.5 border border-zinc-700 hover:border-zinc-500 text-zinc-300 rounded-lg text-xs font-semibold transition"
                    >
                      Save Changes
                    </button>
                    <button
                      onClick={handleConfirmTask}
                      className="px-4 py-1.5 bg-gradient-to-r from-cyan-600 to-purple-600 hover:from-cyan-500 hover:to-purple-500 text-white rounded-lg text-xs font-semibold shadow transition-all flex items-center gap-1"
                    >
                      <Play size={14} />
                      <span>Confirm & Execute Plan</span>
                    </button>
                  </>
                )}

                {activeTask.status === 'executing' && (
                  <button
                    onClick={handleCancelTask}
                    className="px-4 py-1.5 bg-rose-600/90 hover:bg-rose-600 text-white rounded-lg text-xs font-semibold transition flex items-center gap-1"
                  >
                    <Square size={12} fill="white" />
                    <span>Cancel Task</span>
                  </button>
                )}

                {(activeTask.status === 'completed' || activeTask.status === 'failed' || activeTask.status === 'cancelled') && (
                  <button
                    onClick={() => handleSelectTask(activeTask.task_id)}
                    className="px-3 py-1.5 border border-zinc-800 hover:bg-zinc-800 text-zinc-400 rounded-lg text-xs font-semibold transition flex items-center gap-1"
                  >
                    <RotateCw size={12} />
                    <span>Refresh State</span>
                  </button>
                )}
              </div>
            </div>

            {/* User Prompt Box */}
            <div className="p-3 bg-zinc-950/30 rounded-lg border border-zinc-900">
              <span className="text-zinc-500 text-[10px] uppercase font-bold tracking-wider">Client Inquiry:</span>
              <p className="text-sm text-zinc-300 mt-1 italic font-light">"{activeTask.user_query}"</p>
            </div>

            {/* Objective details */}
            {activeTask.plan?.objective && (
              <div className="bg-[#100b21]/60 border border-[#25194f]/50 p-4 rounded-xl">
                <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-wider mb-1">Strategic Objective</h3>
                <p className="text-sm text-zinc-300 leading-relaxed">{activeTask.plan.objective}</p>
              </div>
            )}

            {/* Planning Loader */}
            {activeTask.status === 'planning' && (
              <div className="flex flex-col items-center justify-center p-12 border border-zinc-900 bg-zinc-950/20 rounded-xl gap-4">
                <RotateCw className="animate-spin text-purple-400" size={36} />
                <div className="text-center">
                  <h3 className="font-semibold text-zinc-200">Formulating Plan...</h3>
                  <p className="text-xs text-zinc-500 max-w-xs mt-1">
                    Supervisor is analyzing modalities, dependencies, and generating execution sequences.
                  </p>
                </div>
              </div>
            )}

            {/* Planning Failed View */}
            {activeTask.status === 'planning_failed' && (
              <div className="p-5 border border-rose-950 bg-rose-950/10 rounded-xl space-y-4">
                <div className="flex items-center gap-3">
                  <XCircle className="text-rose-500" size={24} />
                  <div>
                    <h3 className="font-semibold text-zinc-200">Plan Generation Failed</h3>
                    <p className="text-xs text-zinc-500">The Supervisor could not structure the requirements properly.</p>
                  </div>
                </div>
                {activeTask.error && (
                  <div className="bg-zinc-950/40 p-3 rounded font-mono text-xs text-rose-300 border border-zinc-900">
                    <div><strong>Error:</strong> {activeTask.error.message}</div>
                    {activeTask.error.details && <pre className="mt-2 text-[10px] text-zinc-500 overflow-x-auto">{JSON.stringify(activeTask.error.details, null, 2)}</pre>}
                  </div>
                )}
                {/* Editable fallback */}
                <div className="pt-2">
                  <button 
                    onClick={() => {
                      setEditingPlan({
                        title: "Custom Consulting Plan",
                        objective: activeTask.user_query,
                        steps: []
                      });
                      // set state to pending_approval so we can construct a manual plan
                      setActiveTask({...activeTask, status: 'pending_approval'});
                    }} 
                    className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-semibold rounded-lg transition"
                  >
                    Create Custom Plan Manually
                  </button>
                </div>
              </div>
            )}

            {/* Plan steps section */}
            {editingPlan && (
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <h2 className="text-base font-bold text-zinc-200 flex items-center gap-1.5">
                    <span>Task Execution Sequence</span>
                    <span className="text-xs font-mono text-zinc-500">({editingPlan.steps.length} stages)</span>
                  </h2>
                  {activeTask.status === 'pending_approval' && (
                    <button
                      onClick={handleAddStep}
                      className="px-2 py-1 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700/60 text-zinc-300 hover:text-white rounded text-xs font-semibold transition flex items-center gap-1"
                    >
                      <Plus size={12} />
                      <span>Add Stage</span>
                    </button>
                  )}
                </div>

                <div className="space-y-3">
                  {editingPlan.steps.map((step, idx) => {
                    const stepRes: StepResult | undefined = activeTask.step_results[step.step_id];
                    const isReadOnly = activeTask.status !== 'pending_approval';
                    
                    return (
                      <div 
                        key={step.step_id} 
                        className={`p-4 rounded-xl border transition-all ${
                          step.status === 'running' ? 'bg-[#0f1124] border-cyan-500/60 shadow-lg shadow-cyan-950/20' :
                          step.status === 'completed' ? 'bg-zinc-950/20 border-emerald-500/20' :
                          step.status === 'failed' ? 'bg-rose-950/10 border-rose-800/40' :
                          step.status === 'skipped' ? 'bg-zinc-900/10 border-zinc-800/30 opacity-60' :
                          'bg-zinc-900/20 border-zinc-800/70'
                        }`}
                      >
                        {/* Step title header */}
                        <div className="flex justify-between items-start gap-4">
                          <div className="flex items-center gap-2 flex-1 min-w-0">
                            <span className="text-xs font-bold font-mono px-2 py-0.5 bg-zinc-800 border border-zinc-700 rounded text-zinc-400">
                              {step.step_id}
                            </span>
                            
                            {isReadOnly ? (
                              <h3 className="font-semibold text-sm text-zinc-200 truncate">{step.title}</h3>
                            ) : (
                              <input
                                type="text"
                                value={step.title}
                                onChange={(e) => handleEditStepField(idx, 'title', e.target.value)}
                                className="bg-transparent font-semibold text-sm text-zinc-200 border-b border-transparent hover:border-zinc-700 focus:border-cyan-500 focus:outline-none py-0.5 px-1 truncate flex-1"
                              />
                            )}
                          </div>

                          <div className="flex items-center gap-2 shrink-0">
                            <span className={`text-[10px] px-2 py-0.5 rounded font-mono border ${
                              step.status === 'completed' ? 'bg-emerald-950/40 border-emerald-800/50 text-emerald-400' :
                              step.status === 'running' ? 'bg-cyan-950/40 border-cyan-800/50 text-cyan-400 animate-pulse' :
                              step.status === 'failed' ? 'bg-rose-950/40 border-rose-800/50 text-rose-400' :
                              'bg-zinc-900 border-zinc-800 text-zinc-500'
                            }`}>{step.status}</span>

                            {!isReadOnly && (
                              <button 
                                onClick={() => handleDeleteStep(idx)}
                                className="text-zinc-600 hover:text-rose-400 p-1"
                                title="Remove Step"
                              >
                                <Trash2 size={14} />
                              </button>
                            )}

                            {isReadOnly && step.status === 'failed' && (
                              <button
                                onClick={() => handleRetryStep(step.step_id)}
                                className="px-2 py-0.5 bg-cyan-950/40 border border-cyan-800/50 hover:bg-cyan-900/60 text-cyan-400 rounded text-[10px] font-semibold transition flex items-center gap-1"
                                title="Restart step and invalidate dependent downstream steps"
                              >
                                <RotateCw size={10} />
                                <span>Retry</span>
                              </button>
                            )}

                            {isReadOnly && step.status === 'completed' && (
                              <button
                                onClick={() => handleRetryStep(step.step_id)}
                                className="px-1.5 py-0.5 hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300 rounded text-[10px] transition flex items-center gap-1"
                                title="Rerun this completed step (invalidates downstream steps)"
                              >
                                <RotateCw size={10} />
                                <span>Force Rerun</span>
                              </button>
                            )}
                          </div>
                        </div>

                        {/* Step body inputs */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3 pt-3 border-t border-zinc-800/50 text-xs">
                          {/* Left Column: Worker / Instructions */}
                          <div className="space-y-3">
                            <div>
                              <label className="text-zinc-500 font-bold block mb-1">Worker Capability</label>
                              {isReadOnly ? (
                                <span className="font-mono text-zinc-300">{step.worker_name} ({step.output_type})</span>
                              ) : (
                                <div className="flex gap-2">
                                  <select
                                    value={step.worker_name}
                                    onChange={(e) => handleEditStepField(idx, 'worker_name', e.target.value)}
                                    className="bg-[#120e24] border border-zinc-800 rounded p-1 text-zinc-300 focus:outline-none focus:border-cyan-500 w-1/2"
                                  >
                                    <option value="text_worker">text_worker</option>
                                    <option value="image_gen_worker">image_gen_worker</option>
                                    <option value="image_edit_worker">image_edit_worker</option>
                                  </select>
                                  <select
                                    value={step.output_type}
                                    onChange={(e) => handleEditStepField(idx, 'output_type', e.target.value)}
                                    className="bg-[#120e24] border border-zinc-800 rounded p-1 text-zinc-300 focus:outline-none focus:border-cyan-500 w-1/2"
                                  >
                                    <option value="text">Output: text</option>
                                    <option value="image">Output: image</option>
                                    <option value="file">Output: file</option>
                                    <option value="json">Output: json</option>
                                    <option value="mixed">Output: mixed</option>
                                  </select>
                                </div>
                              )}
                            </div>

                            <div>
                              <label className="text-zinc-500 font-bold block mb-1">Instructions</label>
                              {isReadOnly ? (
                                <p className="text-zinc-300 leading-relaxed bg-zinc-950/20 p-2 rounded border border-zinc-900/50">{step.instruction}</p>
                              ) : (
                                <textarea
                                  value={step.instruction}
                                  onChange={(e) => handleEditStepField(idx, 'instruction', e.target.value)}
                                  className="w-full bg-[#120e24] border border-zinc-800 rounded p-2 text-zinc-200 focus:outline-none focus:border-cyan-500"
                                  rows={2}
                                />
                              )}
                            </div>
                          </div>

                          {/* Right Column: Dependencies & Input references */}
                          <div className="space-y-3">
                            <div>
                              <label className="text-zinc-500 font-bold block mb-1">Dependencies (depends_on)</label>
                              {isReadOnly ? (
                                <div className="flex flex-wrap gap-1 mt-1">
                                  {step.depends_on.length === 0 ? (
                                    <span className="text-zinc-600 italic">None</span>
                                  ) : (
                                    step.depends_on.map(dep => (
                                      <span key={dep} className="px-1.5 py-0.5 bg-zinc-800/80 border border-zinc-700 text-zinc-400 rounded font-mono text-[10px]">
                                        {dep}
                                      </span>
                                    ))
                                  )}
                                </div>
                              ) : (
                                <input
                                  type="text"
                                  placeholder="e.g. step_1, step_2"
                                  value={step.depends_on.join(', ')}
                                  onChange={(e) => {
                                    const deps = e.target.value.split(',')
                                      .map(s => s.trim())
                                      .filter(s => s.length > 0);
                                    handleEditStepField(idx, 'depends_on', deps);
                                  }}
                                  className="w-full bg-[#120e24] border border-zinc-800 rounded p-1 text-zinc-200 focus:outline-none focus:border-cyan-500 font-mono"
                                />
                              )}
                            </div>

                            <div>
                              <label className="text-zinc-500 font-bold block mb-1">Input References (input_refs)</label>
                              <div className="space-y-1">
                                {Object.entries(step.input_refs).map(([key, val]) => (
                                  <div key={key} className="flex gap-2 items-center">
                                    <span className="font-semibold text-zinc-400 w-1/4 truncate">{key}:</span>
                                    {isReadOnly ? (
                                      <span className="text-zinc-300 font-mono bg-zinc-950/20 px-1 py-0.5 rounded text-[10px] flex-1 truncate">{val}</span>
                                    ) : (
                                      <>
                                        <input
                                          type="text"
                                          value={val}
                                          onChange={(e) => handleEditInputRef(idx, key, e.target.value)}
                                          placeholder="artifact_step_1_text_0"
                                          className="bg-[#120e24] border border-zinc-800 rounded p-0.5 text-zinc-200 focus:outline-none focus:border-cyan-500 font-mono flex-1 text-[11px]"
                                        />
                                        <button 
                                          onClick={() => handleRemoveInputRef(idx, key)}
                                          className="text-zinc-600 hover:text-zinc-300"
                                        >
                                          &times;
                                        </button>
                                      </>
                                    )}
                                  </div>
                                ))}

                                {!isReadOnly && (
                                  <AddInputRefForm onAdd={(k) => handleAddInputRef(idx, k)} />
                                )}
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Audit execution log (if ran) */}
                        {stepRes && (stepRes.completed_at || stepRes.error) && (
                          <div className="mt-3 pt-3 border-t border-zinc-800/30 text-[11px] font-mono text-zinc-500 flex flex-wrap justify-between items-center gap-2 bg-[#09070e]/50 p-2 rounded">
                            <div>
                              <span>Retries: {stepRes.retry_count}</span>
                              {stepRes.started_at && <span className="ml-3">Ran: {new Date(stepRes.started_at).toLocaleTimeString()} - {stepRes.completed_at ? new Date(stepRes.completed_at).toLocaleTimeString() : ''}</span>}
                            </div>
                            
                            {stepRes.error && (
                              <div className="text-rose-400 flex items-center gap-1 max-w-full">
                                <AlertCircle size={10} />
                                <span className="truncate">[{stepRes.error.error_type}]: {stepRes.error.message}</span>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Deliverables / Artifacts Gallery */}
            {activeTask.artifacts && activeTask.artifacts.length > 0 && (
              <div className="space-y-3 pt-2">
                <h2 className="text-base font-bold text-zinc-200 flex items-center gap-2">
                  <Sparkles size={16} className="text-cyan-400" />
                  <span>Project Deliverables Gallery</span>
                </h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {activeTask.artifacts.map((art) => {
                    const isImg = art.type === 'image';
                    const isText = art.type === 'text';
                    const fullUrl = art.path_or_url.startsWith('http') 
                      ? art.path_or_url 
                      : `http://127.0.0.1:8001/api/files/local/download?filepath=${encodeURIComponent(art.path_or_url)}`;
                    
                    return (
                      <div key={art.artifact_id} className="bg-[#0f0919] border border-zinc-800 rounded-xl overflow-hidden flex flex-col hover:border-zinc-700/80 transition-all">
                        {/* Header info */}
                        <div className="px-3 py-2 bg-zinc-950/40 border-b border-zinc-900 flex justify-between items-center text-xs">
                          <div className="flex items-center gap-1.5 font-mono text-zinc-400">
                            {isImg ? <ImageIcon size={12} className="text-cyan-400" /> : <FileText size={12} className="text-purple-400" />}
                            <span className="font-semibold">{art.artifact_id}</span>
                          </div>
                          <a 
                            href={fullUrl} 
                            target="_blank" 
                            rel="noopener noreferrer" 
                            className="p-1 hover:bg-zinc-800 rounded text-zinc-400 hover:text-cyan-400"
                            title="Download Deliverable"
                            download
                          >
                            <Download size={12} />
                          </a>
                        </div>

                        {/* Rendering content */}
                        <div className="flex-1 flex items-center justify-center bg-zinc-950/20 p-4 min-h-[160px] max-h-[320px] overflow-hidden">
                          {isImg ? (
                            <img 
                              src={fullUrl} 
                              alt={art.artifact_id} 
                              className="max-w-full max-h-56 object-contain rounded hover:scale-105 transition duration-300"
                              onError={(e) => {
                                // Fallback image text if loading fails
                                (e.target as HTMLElement).style.display = 'none';
                              }}
                            />
                          ) : isText ? (
                            <TextArtifactLoader url={fullUrl} />
                          ) : (
                            <div className="text-center text-zinc-600 text-xs">
                              <File size={28} className="mx-auto mb-2 text-zinc-700" />
                              <span>Binary File Reference</span>
                              <div className="text-[10px] text-zinc-500 mt-1 font-mono truncate max-w-[200px]">{art.path_or_url}</div>
                            </div>
                          )}
                        </div>

                        {/* Footer metadata */}
                        {art.metadata && Object.keys(art.metadata).length > 0 && (
                          <div className="p-2 border-t border-zinc-900/50 bg-zinc-950/10 text-[10px] font-mono text-zinc-500 flex justify-between">
                            {art.metadata.prompt && <span className="truncate flex-1 pr-2" title={art.metadata.prompt}>Prompt: {art.metadata.prompt}</span>}
                            {art.metadata.operation && <span className="shrink-0 text-cyan-500">[{art.metadata.operation}]</span>}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Final executive summary */}
            {activeTask.final_summary && (
              <div className="border border-[#2d2258] bg-[#0c071d]/90 p-5 rounded-2xl space-y-3 mt-6 shadow-xl shadow-purple-950/10">
                <div className="flex items-center gap-2 border-b border-zinc-800 pb-3">
                  <Briefcase className="text-purple-400" size={18} />
                  <h2 className="text-base font-bold text-zinc-100">Partner Consulting Report Summary</h2>
                </div>
                
                <div className="text-zinc-300 text-sm leading-relaxed whitespace-pre-wrap font-light">
                  {activeTask.final_summary}
                </div>
              </div>
            )}

            {/* Global Task error message */}
            {activeTask.error && activeTask.status !== 'planning_failed' && (
              <div className="p-4 border border-rose-950 bg-rose-950/10 rounded-xl space-y-2 mt-4 text-xs font-mono text-rose-300">
                <div className="flex items-center gap-2 font-sans font-semibold text-sm text-rose-400">
                  <AlertCircle size={16} />
                  <span>Execution Terminated: Task Failed</span>
                </div>
                <div><strong>Category:</strong> {activeTask.error.error_type}</div>
                <div><strong>Description:</strong> {activeTask.error.message}</div>
                {activeTask.error.details && Object.keys(activeTask.error.details).length > 0 && (
                  <pre className="p-2 bg-zinc-950 rounded mt-1 overflow-x-auto text-[10px] text-zinc-500">
                    {JSON.stringify(activeTask.error.details, null, 2)}
                  </pre>
                )}
              </div>
            )}

            {/* Toggle raw JSON response */}
            <div className="pt-6 border-t border-zinc-800 flex justify-end">
              <button 
                onClick={() => setShowRawJson(!showRawJson)} 
                className="flex items-center gap-1.5 text-zinc-600 hover:text-zinc-400 text-xs transition"
              >
                <Code size={14} />
                <span>{showRawJson ? "Hide" : "Show"} Developer JSON State</span>
              </button>
            </div>

            {showRawJson && (
              <pre className="bg-[#050308] border border-zinc-900 rounded-xl p-4 font-mono text-[10px] text-zinc-500 overflow-x-auto max-h-96">
                {JSON.stringify(activeTask, null, 2)}
              </pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// Subform helper for adding new input refs keys
function AddInputRefForm({ onAdd }: { onAdd: (key: string) => void }) {
  const [val, setVal] = useState('');
  const [open, setOpen] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (val.trim()) {
      onAdd(val.trim());
      setVal('');
      setOpen(false);
    }
  };

  if (!open) {
    return (
      <button 
        type="button" 
        onClick={() => setOpen(true)}
        className="text-zinc-600 hover:text-cyan-400 text-[10px] flex items-center gap-1 mt-1 font-semibold"
      >
        <Plus size={10} />
        <span>Add Input Ref Key</span>
      </button>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-1 items-center mt-1">
      <input
        type="text"
        placeholder="Key (e.g. prompt, base_image)"
        value={val}
        onChange={(e) => setVal(e.target.value)}
        className="bg-[#120e24] border border-zinc-800 rounded px-1.5 py-0.5 text-[10px] text-zinc-200 focus:outline-none focus:border-cyan-500 font-mono flex-1"
        autoFocus
      />
      <button type="submit" className="px-1.5 py-0.5 bg-zinc-800 text-zinc-300 hover:text-white rounded text-[10px]">Add</button>
      <button type="button" onClick={() => setOpen(false)} className="px-1 hover:text-zinc-200 text-[10px]">&times;</button>
    </form>
  );
}

// Subcomponent to fetch and render text file content reactively
function TextArtifactLoader({ url }: { url: string }) {
  const [text, setText] = useState('Loading contents...');
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let active = true;
    const fetchText = async () => {
      try {
        const response = await fetch(url);
        if (response.ok) {
          const txt = await response.text();
          if (active) setText(txt);
        } else {
          if (active) setFailed(true);
        }
      } catch (e) {
        if (active) setFailed(true);
      }
    };
    fetchText();
    return () => { active = false; };
  }, [url]);

  if (failed) {
    return (
      <div className="text-rose-400/80 text-xs italic text-center">
        Failed to fetch text deliverable contents.
      </div>
    );
  }

  return (
    <div className="w-full max-h-56 overflow-y-auto text-xs text-zinc-300 bg-zinc-950/40 p-3 rounded font-light border border-zinc-900/50 leading-relaxed whitespace-pre-wrap font-sans text-left">
      {text}
    </div>
  );
}
