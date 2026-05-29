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
    return {
      success: result.success !== undefined ? result.success : true,
      data: result.data !== undefined ? result.data : result,
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
  }
};
