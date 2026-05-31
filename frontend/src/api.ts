export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface TraceStep {
  node: string;
  status: 'running' | 'completed' | 'failed';
  output?: any;
  timestamp: string;
}

export interface AgentResponse {
  success: boolean;
  provider: string;
  task_type: string;
  data: any;
  trace: TraceStep[];
  error?: string;
}

export interface ProviderInfo {
  name: string;
  is_configured: boolean;
  missing_reason?: string;
  is_active: boolean;
}

export interface LocalFileItem {
  name: string;
  relative_path: string;
  is_dir: boolean;
  size_bytes?: number;
  modified_time: string;
}

export interface PlanStep {
  step_id: string;
  title: string;
  worker_name: string;
  instruction: string;
  depends_on: string[];
  input_refs: Record<string, string>;
  output_type: 'text' | 'image' | 'file' | 'json' | 'mixed';
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped' | 'cancelled';
}

export interface ExecutionPlan {
  title: string;
  objective: string;
  steps: PlanStep[];
}

export interface Artifact {
  artifact_id: string;
  type: 'text' | 'image' | 'file' | 'json' | 'mixed';
  path_or_url: string;
  source_step_id?: string;
  metadata?: Record<string, any>;
}

export interface StepError {
  error_type: 'validation_error' | 'provider_error' | 'worker_error' | 'storage_error' | 'cancelled';
  message: string;
  details?: Record<string, any>;
}

export interface StepResult {
  step_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  output_artifact_ids: string[];
  error?: StepError;
  retry_count: number;
  started_at?: string;
  completed_at?: string;
}

export interface TaskState {
  task_id: string;
  user_query: string;
  status: 'planning' | 'pending_approval' | 'executing' | 'completed' | 'failed' | 'cancelled' | 'planning_failed';
  plan?: ExecutionPlan;
  step_results: Record<string, StepResult>;
  artifacts: Artifact[];
  final_summary?: string;
  error?: StepError;
  created_at: string;
  approved_at?: string;
  started_at?: string;
  completed_at?: string;
  updated_at: string;
}

// Helper to make API requests
async function request<T = any>(url: string, options?: RequestInit): Promise<{ success: boolean; data?: T; error?: string }> {
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers || {})
      }
    });
    const result = await response.json();
    if (!response.ok) {
      return {
        success: false,
        error: result.detail || result.error || response.statusText
      };
    }
    // For AgentResponses containing trace execution information, preserve the root structure
    const isAgentResponse = result.trace !== undefined && result.task_type !== undefined;
    return {
      success: result.success !== undefined ? result.success : true,
      data: (result.data !== undefined && !isAgentResponse) ? result.data : result,
      error: result.error || undefined
    };
  } catch (err: any) {
    return {
      success: false,
      error: err.message || 'Network request failed'
    };
  }
}

export const api = {
  // Agent Endpoint
  async runChat(messages: ChatMessage[], provider?: string) {
    return request<AgentResponse>('/api/agent/chat', {
      method: 'POST',
      body: JSON.stringify({ messages, provider })
    });
  },

  // Settings
  async getProviders() {
    return request<Record<string, ProviderInfo>>('/api/settings/providers');
  },

  async switchProvider(provider: string) {
    return request<{ active_provider: string; message: string }>('/api/settings/providers', {
      method: 'POST',
      body: JSON.stringify({ provider })
    });
  },

  async getWorkspace() {
    return request<{ workspace_root: string; size_limit_mb: number }>('/api/settings/workspace');
  },

  // Media Generation
  async generateImage(prompt: string, provider?: string) {
    return request('/api/media/image-generation', {
      method: 'POST',
      body: JSON.stringify({ prompt, provider })
    });
  },

  async generateVideo(prompt: string, provider?: string) {
    return request('/api/media/video-generation', {
      method: 'POST',
      body: JSON.stringify({ prompt, provider })
    });
  },

  async generateMusic(prompt: string, provider?: string) {
    return request('/api/media/music-generation', {
      method: 'POST',
      body: JSON.stringify({ prompt, provider })
    });
  },

  async generateTTS(text: string, voiceId?: string, provider?: string) {
    return request('/api/media/text-to-speech', {
      method: 'POST',
      body: JSON.stringify({ text, voice_id: voiceId, provider })
    });
  },

  async pollTaskStatus(provider: string, taskType: string, taskId: string) {
    return request(`/api/media/tasks/${provider}/${taskType}/${taskId}`);
  },

  // Local File Safety Agent
  async listLocalFiles(path: string = '') {
    return request<LocalFileItem[]>(`/api/files/local/list?path=${encodeURIComponent(path)}`);
  },

  async readLocalFile(filepath: string) {
    return request<{ content: string; size_bytes: number; relative_path: string }>('/api/files/local/read', {
      method: 'POST',
      body: JSON.stringify({ filepath })
    });
  },

  async writeLocalFile(filepath: string, content: string, dryRun: boolean = true) {
    return request('/api/files/local/write', {
      method: 'POST',
      body: JSON.stringify({ filepath, content, dry_run: dryRun })
    });
  },

  async modifyLocalFile(filepath: string, findStr: string, replaceStr: string, dryRun: boolean = true) {
    return request('/api/files/local/modify', {
      method: 'POST',
      body: JSON.stringify({ filepath, find_str: findStr, replace_str: replaceStr, dry_run: dryRun })
    });
  },

  async deleteLocalFile(filepath: string, dryRun: boolean = true) {
    return request('/api/files/local/delete', {
      method: 'POST',
      body: JSON.stringify({ filepath, dry_run: dryRun })
    });
  },

  // Remote files
  async listRemoteFiles(purpose: string = 'fine-tune') {
    return request(`/api/files/list?purpose=${encodeURIComponent(purpose)}`);
  },

  async deleteRemoteFile(fileId: string) {
    return request(`/api/files/delete/${fileId}`, {
      method: 'DELETE'
    });
  },

  // Consulting Company / Multi-Agent Tasks
  async createTask(userQuery: string) {
    return request<TaskState>('/api/tasks', {
      method: 'POST',
      body: JSON.stringify({ user_query: userQuery })
    });
  },

  async getTask(taskId: string) {
    return request<TaskState>(`/api/tasks/${taskId}`);
  },

  async listTasks() {
    return request<TaskState[]>('/api/tasks');
  },

  async updatePlan(taskId: string, plan: ExecutionPlan) {
    return request<TaskState>(`/api/tasks/${taskId}/plan`, {
      method: 'PUT',
      body: JSON.stringify(plan)
    });
  },

  async confirmTask(taskId: string) {
    return request<TaskState>(`/api/tasks/${taskId}/confirm`, {
      method: 'POST'
    });
  },

  async cancelTask(taskId: string) {
    return request<TaskState>(`/api/tasks/${taskId}/cancel`, {
      method: 'POST'
    });
  },

  async retryStep(taskId: string, stepId: string) {
    return request<TaskState>(`/api/tasks/${taskId}/steps/${stepId}/retry`, {
      method: 'POST'
    });
  }
};
