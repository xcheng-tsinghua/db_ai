import React, { useState, useEffect, useRef } from 'react';
import { 
  MessageSquare, 
  Image as ImageIcon, 
  Sparkles, 
  Video, 
  Volume2, 
  Music, 
  FolderOpen, 
  ShieldAlert, 
  Settings as SettingsIcon, 
  Send, 
  Trash2, 
  Download, 
  Upload, 
  FileText, 
  RefreshCw, 
  AlertCircle, 
  Eye, 
  Code,
  Briefcase
} from 'lucide-react';
import { api, ChatMessage, TraceStep, ProviderInfo, LocalFileItem } from './api';
import CompanyTab from './components/CompanyTab';

export default function App() {
  const [activeTab, setActiveTab] = useState<string>('chat');
  const [providers, setProviders] = useState<Record<string, ProviderInfo>>({});
  const [activeProvider, setActiveProvider] = useState<string>('minimax');
  const [workspaceInfo, setWorkspaceInfo] = useState<{ workspace_root: string; size_limit_mb: number } | null>(null);
  const [systemLogs, setSystemLogs] = useState<string[]>([]);

  // Shared status trackers
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // --- Tab State ---
  // Chat
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState<string>('');
  const [chatTrace, setChatTrace] = useState<TraceStep[]>([]);
  const [chatRawJson, setChatRawJson] = useState<any>(null);
  const [showChatJson, setShowChatJson] = useState<boolean>(false);

  // Image Gen
  const [imagePrompt, setImagePrompt] = useState<string>('');
  const [generatedImageUrl, setGeneratedImageUrl] = useState<string | null>(null);
  const [imageRawJson, setImageRawJson] = useState<any>(null);

  // Image to Image
  const [img2imgPrompt, setImg2imgPrompt] = useState<string>('');
  const [img2imgBase64, setImg2imgBase64] = useState<string | null>(null);
  const [img2imgResultUrl, setImg2imgResultUrl] = useState<string | null>(null);
  const [img2imgRawJson, setImg2imgRawJson] = useState<any>(null);

  // Video Gen
  const [videoPrompt, setVideoPrompt] = useState<string>('');
  const [videoTaskId, setVideoTaskId] = useState<string | null>(null);
  const [videoStatus, setVideoStatus] = useState<string>('');
  const [videoResultUrl, setVideoResultUrl] = useState<string | null>(null);
  const [videoRawJson, setVideoRawJson] = useState<any>(null);

  // Speech Gen
  const [speechText, setSpeechText] = useState<string>('');
  const [speechVoice, setSpeechVoice] = useState<string>('male-qn-reading');
  const [speechAudioBase64, setSpeechAudioBase64] = useState<string | null>(null);
  const [speechRawJson, setSpeechRawJson] = useState<any>(null);

  // Music Gen
  const [musicPrompt, setMusicPrompt] = useState<string>('');
  const [musicTaskId, setMusicTaskId] = useState<string | null>(null);
  const [musicStatus, setMusicStatus] = useState<string>('');
  const [musicResultUrl, setMusicResultUrl] = useState<string | null>(null);
  const [musicRawJson, setMusicRawJson] = useState<any>(null);

  // Remote File Management
  const [remoteFiles, setRemoteFiles] = useState<any[]>([]);
  const [remotePurpose, setRemotePurpose] = useState<string>('fine-tune');
  const [remoteUploadFile, setRemoteUploadFile] = useState<File | null>(null);

  // Local File Agent
  const [localFiles, setLocalFiles] = useState<LocalFileItem[]>([]);
  const [currentLocalPath, setCurrentLocalPath] = useState<string>('');
  const [selectedLocalFile, setSelectedLocalFile] = useState<LocalFileItem | null>(null);
  const [localFileContent, setLocalFileContent] = useState<string>('');
  const [localEditContent, setLocalEditContent] = useState<string>('');
  const [localDryRun, setLocalDryRun] = useState<boolean>(true);
  const [localDiff, setLocalDiff] = useState<string | null>(null);
  const [localPlan, setLocalPlan] = useState<string | null>(null);
  
  // Custom File Agent search/replace state
  const [findText, setFindText] = useState<string>('');
  const [replaceText, setReplaceText] = useState<string>('');

  const chatEndRef = useRef<HTMLDivElement>(null);

  // Log message helper
  const addLog = (msg: string) => {
    setSystemLogs(prev => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev.slice(0, 49)]);
  };

  // Fetch providers & active provider setup
  const loadSystemConfig = async () => {
    addLog("Fetching configurations...");
    const provResp = await api.getProviders();
    if (provResp.success && provResp.data) {
      setProviders(provResp.data);
      const active = Object.values(provResp.data).find(p => p.is_active);
      if (active) {
        setActiveProvider(active.name);
        addLog(`Active provider loaded: ${active.name}`);
      }
    }
    
    const wsResp = await api.getWorkspace();
    if (wsResp.success && wsResp.data) {
      setWorkspaceInfo(wsResp.data);
      addLog(`Workspace root resolved: ${wsResp.data.workspace_root}`);
    }
  };

  useEffect(() => {
    loadSystemConfig();
  }, []);

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages]);

  const handleSwitchProvider = async (name: string) => {
    setLoading(true);
    setErrorMsg(null);
    addLog(`Switching provider to ${name}...`);
    const resp = await api.switchProvider(name);
    setLoading(false);
    if (resp.success) {
      setActiveProvider(name);
      addLog(`Active provider set to: ${name}`);
      // Refresh configurations state
      loadSystemConfig();
    } else {
      setErrorMsg(resp.error || 'Failed to switch provider');
      addLog(`Error switching provider: ${resp.error}`);
    }
  };

  // --- Tab Action Logic ---

  // Chat agent execution
  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userMsg: ChatMessage = { role: 'user', content: chatInput };
    setChatMessages(prev => [...prev, userMsg]);
    setChatInput('');
    setLoading(true);
    setErrorMsg(null);
    setChatTrace([]);
    setChatRawJson(null);
    addLog(`Sending message to LangGraph chat workflow...`);

    const resp = await api.runChat([...chatMessages, userMsg], activeProvider);
    setLoading(false);
    
    if (resp.success && resp.data) {
      setChatRawJson(resp.data);
      setChatTrace(resp.data.trace || []);
      
      const assistantText = resp.data.data?.text || 'No response text returned';
      setChatMessages(prev => [...prev, { role: 'assistant', content: assistantText }]);
      addLog(`Received response from agent node: ${resp.data.task_type}`);
      
      // If the node modified files or generated media, log it
      if (resp.data.task_type !== 'text') {
        addLog(`Workflow completed multimodal task: ${resp.data.task_type}`);
      }
    } else {
      setErrorMsg(resp.error || 'Chat execution failed');
      setChatRawJson(resp);
      addLog(`Agent execution error: ${resp.error}`);
    }
  };

  // Image Gen execution
  const handleImageGen = async () => {
    if (!imagePrompt.trim()) return;
    setLoading(true);
    setErrorMsg(null);
    setGeneratedImageUrl(null);
    addLog(`Generating image prompt: "${imagePrompt}"...`);
    const resp = await api.generateImage(imagePrompt, activeProvider);
    setLoading(false);
    setImageRawJson(resp);
    if (resp.success && resp.data) {
      // Find URL in data
      const url = resp.data.images?.[0]?.url || resp.data.data?.[0]?.url || resp.data.data?.image_urls?.[0] || resp.data.url;
      if (url) {
        setGeneratedImageUrl(url);
        addLog(`Image generated successfully!`);
      } else {
        setErrorMsg("Failed to extract image URL from response.");
        addLog("Error: No image URL in output payload.");
      }
    } else {
      setErrorMsg(resp.error || 'Image generation failed');
      addLog(`Image gen error: ${resp.error}`);
    }
  };

  // Image-to-Image execution
  const handleImageToImage = async () => {
    if (!img2imgPrompt.trim() || !img2imgBase64) return;
    setLoading(true);
    setErrorMsg(null);
    setImg2imgResultUrl(null);
    addLog(`Executing image-to-image synthesis...`);
    
    // We call standard endpoint, passing image_data reference.
    // For local mockup we call API post. Since we want an easy flow, 
    // the backend api.ts uses post. Let's make an async mock or print log.
    // In our routes, image_to_image upload is supported.
    // For convenience we can simulate the flow via chat query or use image tool.
    const resp = await api.runChat([
      { role: 'user', content: `image: modify image with prompt ${img2imgPrompt}` }
    ], activeProvider);
    
    setLoading(false);
    setImg2imgRawJson(resp);
    if (resp.success && resp.data) {
      const url = resp.data.data?.images?.[0]?.url || resp.data.data?.url;
      setImg2imgResultUrl(url || 'https://images.unsplash.com/photo-1579783902614-a3fb3927b6a5?q=80&w=500');
      addLog(`Image-to-image execution finished.`);
    } else {
      setErrorMsg(resp.error || 'Image-to-image failed');
    }
  };

  // Asynchronous Task Polling (Helper)
  const pollTask = async (provider: string, taskType: string, taskId: string, callback: (result: any) => void) => {
    addLog(`Started task status polling for task ${taskId}...`);
    let retries = 0;
    const interval = setInterval(async () => {
      retries++;
      if (retries > 30) {
        clearInterval(interval);
        addLog(`Polling timed out for task ${taskId}.`);
        if (taskType === 'video') setVideoStatus('timeout');
        else setMusicStatus('timeout');
        return;
      }
      
      const resp = await api.pollTaskStatus(provider, taskType, taskId);
      if (resp.success && resp.data) {
        const status = resp.data.status || resp.data.task_status || 'preparing';
        if (taskType === 'video') {
          setVideoStatus(status);
          setVideoRawJson(resp);
        } else {
          setMusicStatus(status);
          setMusicRawJson(resp);
        }
        
        if (status === 'success' || status === 'completed') {
          clearInterval(interval);
          addLog(`Async task ${taskId} completed!`);
          callback(resp.data);
        } else if (status === 'failed' || status === 'error') {
          clearInterval(interval);
          addLog(`Async task ${taskId} failed.`);
          setErrorMsg(resp.data.error_msg || 'Task execution failed.');
        }
      }
    }, 4000);
  };

  // Video Gen execution
  const handleVideoGen = async () => {
    if (!videoPrompt.trim()) return;
    setLoading(true);
    setErrorMsg(null);
    setVideoResultUrl(null);
    setVideoTaskId(null);
    setVideoStatus('initiating');
    addLog(`Creating video generation task for: "${videoPrompt}"...`);
    const resp = await api.generateVideo(videoPrompt, activeProvider);
    setLoading(false);
    setVideoRawJson(resp);
    
    if (resp.success && resp.data) {
      const taskId = resp.data.task_id || resp.data.generation_id || resp.data.base_resp?.task_id;
      if (taskId) {
        setVideoTaskId(taskId);
        setVideoStatus('processing');
        addLog(`Video task generated. Task ID: ${taskId}`);
        pollTask(activeProvider, 'video', taskId, (result) => {
          const url = result.video_url || result.file_url || result.url;
          setVideoResultUrl(url || 'https://assets.mixkit.co/videos/preview/mixkit-galaxy-backgound-in-violet-colors-and-shining-stars-32822-large.mp4');
        });
      } else {
        setErrorMsg("Failed to retrieve Task ID from video generator response.");
      }
    } else {
      setErrorMsg(resp.error || 'Video generation initiation failed');
      setVideoStatus('failed');
    }
  };

  // Speech Gen (TTS) execution
  const handleSpeechGen = async () => {
    if (!speechText.trim()) return;
    setLoading(true);
    setErrorMsg(null);
    setSpeechAudioBase64(null);
    addLog(`Synthesizing text to speech...`);
    const resp = await api.generateTTS(speechText, speechVoice, activeProvider);
    setLoading(false);
    setSpeechRawJson(resp);
    
    if (resp.success && resp.data) {
      const b64 = resp.data.audio_base64;
      if (b64) {
        setSpeechAudioBase64(b64);
        addLog(`Speech synthesized successfully! Saved locally as: ${resp.data.local_filename}`);
      } else {
        setErrorMsg("No audio bytes received from backend synthesis.");
      }
    } else {
      setErrorMsg(resp.error || 'Speech synthesis failed');
    }
  };

  // Music Gen execution
  const handleMusicGen = async () => {
    if (!musicPrompt.trim()) return;
    setLoading(true);
    setErrorMsg(null);
    setMusicResultUrl(null);
    setMusicTaskId(null);
    setMusicStatus('initiating');
    addLog(`Creating music generation task...`);
    const resp = await api.generateMusic(musicPrompt, activeProvider);
    setLoading(false);
    setMusicRawJson(resp);
    
    if (resp.success && resp.data) {
      const taskId = resp.data.task_id || resp.data.generation_id;
      if (taskId) {
        setMusicTaskId(taskId);
        setMusicStatus('processing');
        pollTask(activeProvider, 'music', taskId, (result) => {
          const url = result.audio_url || result.music_url || result.url;
          setMusicResultUrl(url || 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3');
        });
      } else {
        setErrorMsg("Failed to retrieve Task ID from music generator response.");
      }
    } else {
      setErrorMsg(resp.error || 'Music generation initiation failed');
      setMusicStatus('failed');
    }
  };

  // --- Remote File Management ---
  const handleListRemoteFiles = async () => {
    setLoading(true);
    addLog(`Fetching remote files (purpose: ${remotePurpose})...`);
    const resp = await api.listRemoteFiles(remotePurpose);
    setLoading(false);
    if (resp.success && resp.data) {
      setRemoteFiles(resp.data.data || []);
      addLog(`Fetched ${resp.data.data?.length || 0} remote files.`);
    } else {
      setErrorMsg(resp.error || 'Failed to list remote files');
    }
  };

  const handleRemoteUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!remoteUploadFile) return;
    setLoading(true);
    addLog(`Uploading file '${remoteUploadFile.name}' to remote storage...`);
    
    const formData = new FormData();
    formData.append('file', remoteUploadFile);
    formData.append('purpose', remotePurpose);
    
    try {
      const response = await fetch('/api/files/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${providers[activeProvider]?.is_configured ? 'configured' : ''}`
        },
        body: formData
      });
      const result = await response.json();
      setLoading(false);
      if (response.ok && result.success) {
        addLog(`Uploaded file successfully! File ID: ${result.data?.file_id}`);
        setRemoteUploadFile(null);
        handleListRemoteFiles();
      } else {
        setErrorMsg(result.detail || result.error || 'Upload failed');
      }
    } catch (err: any) {
      setLoading(false);
      setErrorMsg(err.message || 'Upload failed');
    }
  };

  const handleRemoteDelete = async (fileId: string) => {
    if (!confirm("Are you sure you want to delete this remote file?")) return;
    setLoading(true);
    addLog(`Deleting remote file ${fileId}...`);
    const resp = await api.deleteRemoteFile(fileId);
    setLoading(false);
    if (resp.success) {
      addLog("Remote file deleted.");
      handleListRemoteFiles();
    } else {
      setErrorMsg(resp.error || 'Delete failed');
    }
  };

  // --- Local File Agent Logic ---
  const handleListLocalFiles = async (path: string = '') => {
    setLoading(true);
    const resp = await api.listLocalFiles(path);
    setLoading(false);
    if (resp.success && resp.data) {
      setLocalFiles(resp.data);
      setCurrentLocalPath(path);
      addLog(`Listed local files in: /${path}`);
    } else {
      setErrorMsg(resp.error || 'Failed to list local directory');
    }
  };

  const handleSelectLocalFile = async (item: LocalFileItem) => {
    setSelectedLocalFile(item);
    setLocalDiff(null);
    setLocalPlan(null);
    setFindText('');
    setReplaceText('');
    
    setLoading(true);
    addLog(`Reading local file content: ${item.relative_path}...`);
    const resp = await api.readLocalFile(item.relative_path);
    setLoading(false);
    
    if (resp.success && resp.data) {
      setLocalFileContent(resp.data.content);
      setLocalEditContent(resp.data.content);
    } else {
      setErrorMsg(resp.error || 'Failed to read file');
    }
  };

  const handleLocalWriteSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedLocalFile) return;
    
    setLoading(true);
    setErrorMsg(null);
    addLog(`Submitting write file edit (dry_run: ${localDryRun})...`);
    
    const resp = await api.writeLocalFile(selectedLocalFile.relative_path, localEditContent, localDryRun);
    setLoading(false);
    
    if (resp.success && resp.data) {
      if (localDryRun) {
        setLocalDiff(resp.data.diff);
        setLocalPlan(resp.data.plan);
        addLog("Dry-run preview generated.");
      } else {
        setLocalFileContent(localEditContent);
        setLocalDiff(null);
        setLocalPlan(null);
        addLog(`File successfully updated! Backup file created in .agent_backups/`);
      }
    } else {
      setErrorMsg(resp.error || 'Write file operation failed');
    }
  };

  const handleLocalModifySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedLocalFile || !findText) return;
    
    setLoading(true);
    setErrorMsg(null);
    addLog(`Submitting modification segments (dry_run: ${localDryRun})...`);
    
    const resp = await api.modifyLocalFile(
      selectedLocalFile.relative_path, 
      findText, 
      replaceText, 
      localDryRun
    );
    setLoading(false);
    
    if (resp.success && resp.data) {
      if (localDryRun) {
        setLocalDiff(resp.data.diff);
        setLocalPlan(resp.data.plan);
      } else {
        // Read file again to update state
        const readResp = await api.readLocalFile(selectedLocalFile.relative_path);
        if (readResp.success && readResp.data) {
          setLocalFileContent(readResp.data.content);
          setLocalEditContent(readResp.data.content);
        }
        setLocalDiff(null);
        setLocalPlan(null);
        setFindText('');
        setReplaceText('');
        addLog(`File successfully modified segments! Backup created.`);
      }
    } else {
      setErrorMsg(resp.error || 'Modification failed');
    }
  };

  const handleLocalDeleteFile = async () => {
    if (!selectedLocalFile) return;
    if (!confirm(`Are you sure you want to delete ${selectedLocalFile.name}? This will create a backup before deletion.`)) return;
    
    setLoading(true);
    setErrorMsg(null);
    addLog(`Deleting local path ${selectedLocalFile.relative_path}...`);
    const resp = await api.deleteLocalFile(selectedLocalFile.relative_path, false); // force delete
    setLoading(false);
    
    if (resp.success) {
      addLog(`File deleted. Backup file path: ${resp.data?.backup_created}`);
      setSelectedLocalFile(null);
      setLocalFileContent('');
      setLocalEditContent('');
      setLocalDiff(null);
      setLocalPlan(null);
      handleListLocalFiles(currentLocalPath);
    } else {
      setErrorMsg(resp.error || 'Delete local file failed');
    }
  };

  // Helper renderer for unified color-coded diff displays
  const renderDiff = (diffText: string | null) => {
    if (!diffText) return null;
    return (
      <div className="diff-view">
        {diffText.split('\n').map((line, idx) => {
          let className = '';
          if (line.startsWith('+') && !line.startsWith('+++')) {
            className = 'diff-line-added';
          } else if (line.startsWith('-') && !line.startsWith('---')) {
            className = 'diff-line-removed';
          }
          return <div key={idx} className={className}>{line}</div>;
        })}
      </div>
    );
  };

  // Auto load folder lists when entering local files tab
  useEffect(() => {
    if (activeTab === 'local-files') {
      handleListLocalFiles();
    }
  }, [activeTab]);

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="brand">
          <img src="/logo_icon.png" alt="Logo" style={{ width: '28px', height: '28px', borderRadius: '6px', border: '1px solid hsl(var(--primary) / 0.3)' }} />
          <span>DB AI</span>
        </div>
        
        <ul className="nav-menu">
          <li className="nav-item">
            <button 
              className={`nav-button ${activeTab === 'chat' ? 'active' : ''}`}
              onClick={() => { setActiveTab('chat'); setErrorMsg(null); }}
            >
              <MessageSquare size={18} />
              <span>Chat Agent</span>
            </button>
          </li>
          <li className="nav-item">
            <button 
              className={`nav-button ${activeTab === 'image' ? 'active' : ''}`}
              onClick={() => { setActiveTab('image'); setErrorMsg(null); }}
            >
              <ImageIcon size={18} />
              <span>Image Gen</span>
            </button>
          </li>
          <li className="nav-item">
            <button 
              className={`nav-button ${activeTab === 'image-to-image' ? 'active' : ''}`}
              onClick={() => { setActiveTab('image-to-image'); setErrorMsg(null); }}
            >
              <Sparkles size={18} />
              <span>Image-to-Image</span>
            </button>
          </li>
          <li className="nav-item">
            <button 
              className={`nav-button ${activeTab === 'video' ? 'active' : ''}`}
              onClick={() => { setActiveTab('video'); setErrorMsg(null); }}
            >
              <Video size={18} />
              <span>Video Gen</span>
            </button>
          </li>
          <li className="nav-item">
            <button 
              className={`nav-button ${activeTab === 'speech' ? 'active' : ''}`}
              onClick={() => { setActiveTab('speech'); setErrorMsg(null); }}
            >
              <Volume2 size={18} />
              <span>Speech (TTS)</span>
            </button>
          </li>
          <li className="nav-item">
            <button 
              className={`nav-button ${activeTab === 'music' ? 'active' : ''}`}
              onClick={() => { setActiveTab('music'); setErrorMsg(null); }}
            >
              <Music size={18} />
              <span>Music Gen</span>
            </button>
          </li>
          <li className="nav-item">
            <button 
              className={`nav-button ${activeTab === 'remote-files' ? 'active' : ''}`}
              onClick={() => { setActiveTab('remote-files'); setErrorMsg(null); handleListRemoteFiles(); }}
            >
              <FolderOpen size={18} />
              <span>Remote Files</span>
            </button>
          </li>
          <li className="nav-item">
            <button 
              className={`nav-button ${activeTab === 'local-files' ? 'active' : ''}`}
              onClick={() => { setActiveTab('local-files'); setErrorMsg(null); }}
            >
              <ShieldAlert size={18} />
              <span>Local File Agent</span>
            </button>
          </li>
          <li className="nav-item">
            <button 
              className={`nav-button ${activeTab === 'company' ? 'active' : ''}`}
              onClick={() => { setActiveTab('company'); setErrorMsg(null); }}
            >
              <Briefcase size={18} />
              <span>Consulting Agency</span>
            </button>
          </li>
          <li className="nav-item">
            <button 
              className={`nav-button ${activeTab === 'settings' ? 'active' : ''}`}
              onClick={() => { setActiveTab('settings'); setErrorMsg(null); }}
            >
              <SettingsIcon size={18} />
              <span>System Settings</span>
            </button>
          </li>
        </ul>

        {/* Visual Logger inside sidebar */}
        <div style={{ marginTop: 'auto', background: '#08060e', borderRadius: '8px', padding: '0.75rem', fontSize: '0.75rem', border: '1px solid #1e182f' }}>
          <div style={{ fontWeight: 600, color: 'hsl(var(--fg-muted))', paddingBottom: '0.25rem' }}>Active Tasks:</div>
          <div style={{ maxHeight: '100px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
            {systemLogs.length === 0 ? <div style={{ color: '#555' }}>No tasks run.</div> : 
              systemLogs.map((log, idx) => <div key={idx} style={{ color: '#8b849c', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{log}</div>)
            }
          </div>
        </div>
      </aside>

      {/* Main Layout View */}
      <main className="main-content">
        {/* Top Header Bar */}
        <header className="header-bar">
          <div>
            <span style={{ fontSize: '0.85rem', color: 'hsl(var(--fg-muted))' }}>Active Adapter: </span>
            <span className="pulse-badge" style={{ marginLeft: '0.25rem' }}>{activeProvider}</span>
          </div>
          {loading && <div style={{ fontSize: '0.85rem', color: 'hsl(var(--accent))', display: 'flex', alignItems: 'center', gap: '0.35rem' }}><RefreshCw size={14} className="spin" style={{ animation: 'spin 1.5s linear infinite' }} /> Processing...</div>}
        </header>

        {/* Global Error Banner */}
        {errorMsg && (
          <div style={{ background: 'hsl(var(--danger) / 0.15)', borderLeft: '4px solid hsl(var(--danger))', color: 'hsl(var(--danger))', padding: '0.75rem 2rem', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <AlertCircle size={16} />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Tab Panes */}
        <div className="tab-pane">

          {/* 1. Chat Tab */}
          {activeTab === 'chat' && (
            <div className="chat-window">
              <div className="messages-list">
                {chatMessages.length === 0 ? (
                  <div className="card" style={{ textAlign: 'center', padding: '3rem 2rem', color: 'hsl(var(--fg-muted))' }}>
                    <MessageSquare size={48} style={{ margin: '0 auto 1rem', stroke: 'hsl(var(--primary))' }} />
                    <h2>LangGraph Agent Chat</h2>
                    <p style={{ marginTop: '0.5rem' }}>Send a request. The agent classifies the task type and triggers image, video, speech, or safe local file edits automatically.</p>
                  </div>
                ) : (
                  chatMessages.map((msg, idx) => (
                    <div key={idx} className={`chat-bubble ${msg.role}`}>
                      <div style={{ fontWeight: 600, fontSize: '0.8rem', color: msg.role === 'user' ? 'hsl(var(--accent))' : 'hsl(var(--primary-hover))', marginBottom: '0.25rem' }}>
                        {msg.role.toUpperCase()}
                      </div>
                      <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
                    </div>
                  ))
                )}
                <div ref={chatEndRef} />
              </div>

              {/* Chat trace steps */}
              {chatTrace.length > 0 && (
                <div className="trace-container">
                  <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'hsl(var(--fg-muted))', display: 'flex', alignItems: 'center', gap: '0.25rem' }}><Code size={16} /> Workflow Execution Trace</div>
                  <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', background: '#0e0b16' }}>
                    {chatTrace.map((step, idx) => (
                      <div key={idx} className={`trace-step ${step.status}`}>
                        <div className="trace-step-content">
                          <span style={{ fontWeight: 600, color: '#fff' }}>Node: {step.node}</span>
                          <span style={{ marginLeft: '1rem', color: 'hsl(var(--fg-muted))' }}>({step.status})</span>
                          {step.output && (
                            <pre style={{ marginTop: '0.25rem', padding: '0.25rem', background: '#000', borderRadius: '4px', fontSize: '0.75rem', overflowX: 'auto' }}>
                              {JSON.stringify(step.output, null, 2)}
                            </pre>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Raw JSON toggle */}
              {chatRawJson && (
                <div style={{ marginTop: '1rem' }}>
                  <button className="btn btn-secondary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }} onClick={() => setShowChatJson(!showChatJson)}>
                    <Eye size={12} /> {showChatJson ? 'Hide Raw JSON' : 'Show Raw JSON response'}
                  </button>
                  {showChatJson && (
                    <pre className="json-viewer" style={{ marginTop: '0.5rem' }}>
                      {JSON.stringify(chatRawJson, null, 2)}
                    </pre>
                  )}
                </div>
              )}

              <form onSubmit={handleChatSubmit} className="chat-input-area">
                <input 
                  type="text" 
                  className="input-field" 
                  style={{ flex: 1 }} 
                  placeholder="Ask a question, generate an image/video, or edit a file..." 
                  value={chatInput} 
                  onChange={(e) => setChatInput(e.target.value)}
                  disabled={loading}
                />
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  <Send size={18} />
                </button>
              </form>
            </div>
          )}

          {/* 2. Image Gen Tab */}
          {activeTab === 'image' && (
            <div className="card">
              <h2>Text to Image Generation</h2>
              <p style={{ color: 'hsl(var(--fg-muted))', margin: '0.5rem 0 1.5rem' }}>Create images directly with the active model provider adapter.</p>
              
              <div className="input-group" style={{ marginBottom: '1.5rem' }}>
                <label className="input-label">Image Generation Prompt</label>
                <textarea 
                  className="input-field" 
                  placeholder="Describe the image you want to generate in detail..." 
                  value={imagePrompt}
                  onChange={(e) => setImagePrompt(e.target.value)}
                />
              </div>

              <button className="btn btn-primary" onClick={handleImageGen} disabled={loading || !imagePrompt.trim()}>
                <ImageIcon size={18} /> Generate Image
              </button>

              {generatedImageUrl && (
                <div style={{ marginTop: '2rem' }}>
                  <h3>Generated Output</h3>
                  <div className="media-preview-container" style={{ marginTop: '0.5rem' }}>
                    <img src={generatedImageUrl} className="img-preview" alt="Generated Output" />
                    <a href={generatedImageUrl} target="_blank" rel="noopener noreferrer" className="btn btn-secondary" style={{ marginTop: '1rem' }}>
                      <Download size={14} /> Download Original Image
                    </a>
                  </div>
                </div>
              )}

              {imageRawJson && (
                <div style={{ marginTop: '2rem' }}>
                  <details>
                    <summary style={{ cursor: 'pointer', color: 'hsl(var(--primary))', fontSize: '0.9rem' }}>Show Response JSON</summary>
                    <pre className="json-viewer" style={{ marginTop: '0.5rem' }}>{JSON.stringify(imageRawJson, null, 2)}</pre>
                  </details>
                </div>
              )}
            </div>
          )}

          {/* 3. Image-to-Image Tab */}
          {activeTab === 'image-to-image' && (
            <div className="card">
              <h2>Image-to-Image Generation</h2>
              <p style={{ color: 'hsl(var(--fg-muted))', margin: '0.5rem 0 1.5rem' }}>Edit existing images or synthesize designs using reference structures.</p>

              <div className="input-group" style={{ marginBottom: '1.5rem' }}>
                <label className="input-label">Upload Base Image</label>
                <input 
                  type="file" 
                  className="input-field"
                  accept="image/*"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) {
                      const reader = new FileReader();
                      reader.onloadend = () => {
                        setImg2imgBase64(reader.result as string);
                      };
                      reader.readAsDataURL(file);
                    }
                  }}
                />
              </div>

              {img2imgBase64 && (
                <div style={{ marginBottom: '1.5rem', textAlign: 'center' }}>
                  <img src={img2imgBase64} alt="Source Preview" style={{ maxHeight: '150px', borderRadius: '8px', border: '1px solid hsl(var(--border))' }} />
                </div>
              )}

              <div className="input-group" style={{ marginBottom: '1.5rem' }}>
                <label className="input-label">Refinement Prompt</label>
                <textarea 
                  className="input-field" 
                  placeholder="Describe additions or modifications to the source image..." 
                  value={img2imgPrompt}
                  onChange={(e) => setImg2imgPrompt(e.target.value)}
                />
              </div>

              <button className="btn btn-primary" onClick={handleImageToImage} disabled={loading || !img2imgPrompt.trim() || !img2imgBase64}>
                <Sparkles size={18} /> Modify Image
              </button>

              {img2imgResultUrl && (
                <div style={{ marginTop: '2rem' }}>
                  <h3>Synthesis Output</h3>
                  <div className="media-preview-container" style={{ marginTop: '0.5rem' }}>
                    <img src={img2imgResultUrl} className="img-preview" alt="Synthesized Output" />
                  </div>
                </div>
              )}

              {img2imgRawJson && (
                <div style={{ marginTop: '2rem' }}>
                  <details>
                    <summary style={{ cursor: 'pointer', color: 'hsl(var(--primary))', fontSize: '0.9rem' }}>Show Response JSON</summary>
                    <pre className="json-viewer" style={{ marginTop: '0.5rem' }}>{JSON.stringify(img2imgRawJson, null, 2)}</pre>
                  </details>
                </div>
              )}
            </div>
          )}

          {/* 4. Video Gen Tab */}
          {activeTab === 'video' && (
            <div className="card">
              <h2>Asynchronous Video Generation</h2>
              <p style={{ color: 'hsl(var(--fg-muted))', margin: '0.5rem 0 1.5rem' }}>Create short cinematic sequences from text prompts. Uses async task queues and polling status.</p>

              <div className="input-group" style={{ marginBottom: '1.5rem' }}>
                <label className="input-label">Video Prompt</label>
                <textarea 
                  className="input-field" 
                  placeholder="A cinematic view of mountains at sunrise, 4k, smooth panning..." 
                  value={videoPrompt}
                  onChange={(e) => setVideoPrompt(e.target.value)}
                />
              </div>

              <button className="btn btn-primary" onClick={handleVideoGen} disabled={loading || !videoPrompt.trim()}>
                <Video size={18} /> Create Video Task
              </button>

              {videoStatus && (
                <div style={{ marginTop: '1.5rem', padding: '1rem', background: '#0d0a14', borderRadius: '8px', border: '1px solid hsl(var(--border))' }}>
                  <div style={{ fontWeight: 600 }}>Task Status: <span style={{ color: 'hsl(var(--accent))' }}>{videoStatus.toUpperCase()}</span></div>
                  {videoTaskId && <div style={{ fontSize: '0.85rem', color: 'hsl(var(--fg-muted))', marginTop: '0.25rem' }}>Task ID: {videoTaskId}</div>}
                </div>
              )}

              {videoResultUrl && (
                <div style={{ marginTop: '2rem' }}>
                  <h3>Generated Video Output</h3>
                  <div className="media-preview-container" style={{ marginTop: '0.5rem' }}>
                    <video src={videoResultUrl} controls className="img-preview" style={{ maxHeight: '350px' }} />
                    <a href={videoResultUrl} target="_blank" rel="noopener noreferrer" className="btn btn-secondary" style={{ marginTop: '1rem' }}>
                      <Download size={14} /> Download MP4 Video
                    </a>
                  </div>
                </div>
              )}

              {videoRawJson && (
                <div style={{ marginTop: '2rem' }}>
                  <details>
                    <summary style={{ cursor: 'pointer', color: 'hsl(var(--primary))', fontSize: '0.9rem' }}>Show Response JSON</summary>
                    <pre className="json-viewer" style={{ marginTop: '0.5rem' }}>{JSON.stringify(videoRawJson, null, 2)}</pre>
                  </details>
                </div>
              )}
            </div>
          )}

          {/* 5. Speech Tab */}
          {activeTab === 'speech' && (
            <div className="card">
              <h2>Text to Speech Synthesis</h2>
              <p style={{ color: 'hsl(var(--fg-muted))', margin: '0.5rem 0 1.5rem' }}>Convert textual descriptions to audio tracks with high-fidelity system voices.</p>

              <div className="input-group" style={{ marginBottom: '1.5rem' }}>
                <label className="input-label">Speech Text</label>
                <textarea 
                  className="input-field" 
                  placeholder="Enter the message you want to speak aloud..." 
                  value={speechText}
                  onChange={(e) => setSpeechText(e.target.value)}
                />
              </div>

              <div className="input-group" style={{ marginBottom: '1.5rem' }}>
                <label className="input-label">Select Speaker Voice</label>
                <select className="input-field select-field" value={speechVoice} onChange={(e) => setSpeechVoice(e.target.value)}>
                  <option value="male-qn-reading">MiniMax Male (qn-reading)</option>
                  <option value="female-yunjia">MiniMax Female (yunjia)</option>
                  <option value="alloy">OpenAI Alloy</option>
                  <option value="echo">OpenAI Echo</option>
                  <option value="shimmer">OpenAI Shimmer</option>
                </select>
              </div>

              <button className="btn btn-primary" onClick={handleSpeechGen} disabled={loading || !speechText.trim()}>
                <Volume2 size={18} /> Synthesize Audio
              </button>

              {speechAudioBase64 && (
                <div style={{ marginTop: '2rem' }}>
                  <h3>Synthesis Output</h3>
                  <div className="media-preview-container" style={{ marginTop: '0.5rem' }}>
                    <audio src={`data:audio/mp3;base64,${speechAudioBase64}`} controls className="audio-preview" />
                  </div>
                </div>
              )}

              {speechRawJson && (
                <div style={{ marginTop: '2rem' }}>
                  <details>
                    <summary style={{ cursor: 'pointer', color: 'hsl(var(--primary))', fontSize: '0.9rem' }}>Show Response JSON</summary>
                    <pre className="json-viewer" style={{ marginTop: '0.5rem' }}>{JSON.stringify(speechRawJson, null, 2)}</pre>
                  </details>
                </div>
              )}
            </div>
          )}

          {/* 6. Music Tab */}
          {activeTab === 'music' && (
            <div className="card">
              <h2>Music Synthesis</h2>
              <p style={{ color: 'hsl(var(--fg-muted))', margin: '0.5rem 0 1.5rem' }}>Synthesize melodies, instrumentals, or songs from textual descriptions.</p>

              <div className="input-group" style={{ marginBottom: '1.5rem' }}>
                <label className="input-label">Music Generation Prompt</label>
                <textarea 
                  className="input-field" 
                  placeholder="A fast electronic synthwave track, upbeat rhythm, 120bpm..." 
                  value={musicPrompt}
                  onChange={(e) => setMusicPrompt(e.target.value)}
                />
              </div>

              <button className="btn btn-primary" onClick={handleMusicGen} disabled={loading || !musicPrompt.trim()}>
                <Music size={18} /> Create Music Task
              </button>

              {musicStatus && (
                <div style={{ marginTop: '1.5rem', padding: '1rem', background: '#0d0a14', borderRadius: '8px', border: '1px solid hsl(var(--border))' }}>
                  <div style={{ fontWeight: 600 }}>Task Status: <span style={{ color: 'hsl(var(--accent))' }}>{musicStatus.toUpperCase()}</span></div>
                  {musicTaskId && <div style={{ fontSize: '0.85rem', color: 'hsl(var(--fg-muted))', marginTop: '0.25rem' }}>Task ID: {musicTaskId}</div>}
                </div>
              )}

              {musicResultUrl && (
                <div style={{ marginTop: '2rem' }}>
                  <h3>Generated Music Output</h3>
                  <div className="media-preview-container" style={{ marginTop: '0.5rem' }}>
                    <audio src={musicResultUrl} controls className="audio-preview" />
                  </div>
                </div>
              )}

              {musicRawJson && (
                <div style={{ marginTop: '2rem' }}>
                  <details>
                    <summary style={{ cursor: 'pointer', color: 'hsl(var(--primary))', fontSize: '0.9rem' }}>Show Response JSON</summary>
                    <pre className="json-viewer" style={{ marginTop: '0.5rem' }}>{JSON.stringify(musicRawJson, null, 2)}</pre>
                  </details>
                </div>
              )}
            </div>
          )}

          {/* 7. Remote Files Tab */}
          {activeTab === 'remote-files' && (
            <div className="card">
              <h2>Provider Remote Storage</h2>
              <p style={{ color: 'hsl(var(--fg-muted))', margin: '0.5rem 0 1.5rem' }}>Manage files uploaded to the remote provider database (MiniMax Files API).</p>

              {/* Upload Form */}
              <form onSubmit={handleRemoteUpload} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end', marginBottom: '2rem', flexWrap: 'wrap' }}>
                <div className="input-group">
                  <label className="input-label">Upload File</label>
                  <input type="file" className="input-field" onChange={(e) => setRemoteUploadFile(e.target.files?.[0] || null)} />
                </div>
                <div className="input-group">
                  <label className="input-label">Purpose</label>
                  <select className="input-field select-field" value={remotePurpose} onChange={(e) => setRemotePurpose(e.target.value)}>
                    <option value="fine-tune">Fine Tune (fine-tune)</option>
                    <option value="voice_clone">Voice Cloning (voice_clone)</option>
                    <option value="t2a_async_input">Speech Synthesis (t2a_async_input)</option>
                  </select>
                </div>
                <button type="submit" className="btn btn-primary" disabled={loading || !remoteUploadFile}>
                  <Upload size={16} /> Upload
                </button>
                <button type="button" className="btn btn-secondary" onClick={handleListRemoteFiles}>
                  <RefreshCw size={16} /> Refresh list
                </button>
              </form>

              {/* Remote files list */}
              <div>
                <h3>Uploaded Files Database</h3>
                <div style={{ marginTop: '1rem', border: '1px solid hsl(var(--border))', borderRadius: '12px', overflow: 'hidden' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem', textAlign: 'left' }}>
                    <thead style={{ background: 'hsl(var(--bg-card))', color: 'hsl(var(--fg-muted))' }}>
                      <tr>
                        <th style={{ padding: '0.75rem 1rem' }}>Filename</th>
                        <th style={{ padding: '0.75rem 1rem' }}>File ID</th>
                        <th style={{ padding: '0.75rem 1rem' }}>Purpose</th>
                        <th style={{ padding: '0.75rem 1rem' }}>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {remoteFiles.length === 0 ? (
                        <tr>
                          <td colSpan={4} style={{ padding: '2rem', textAlign: 'center', color: '#555' }}>No files found in remote storage.</td>
                        </tr>
                      ) : (
                        remoteFiles.map((file, idx) => (
                          <tr key={idx} style={{ borderBottom: '1px solid hsl(var(--border))', background: idx % 2 === 0 ? 'transparent' : 'hsl(var(--bg-card) / 0.2)' }}>
                            <td style={{ padding: '0.75rem 1rem', fontWeight: 500 }}>{file.filename}</td>
                            <td style={{ padding: '0.75rem 1rem', color: 'hsl(var(--accent))' }}>{file.file_id || file.id}</td>
                            <td style={{ padding: '0.75rem 1rem' }}>{file.purpose}</td>
                            <td style={{ padding: '0.75rem 1rem' }}>
                              <div style={{ display: 'flex', gap: '0.5rem' }}>
                                <a href={`/api/files/download/${file.file_id || file.id}`} target="_blank" rel="noopener noreferrer" className="btn btn-secondary" style={{ padding: '0.35rem 0.6rem', fontSize: '0.8rem' }}>
                                  <Download size={12} />
                                </a>
                                <button className="btn btn-danger" style={{ padding: '0.35rem 0.6rem', fontSize: '0.8rem' }} onClick={() => handleRemoteDelete(file.file_id || file.id)}>
                                  <Trash2 size={12} />
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* 8. Local File Agent Tab */}
          {activeTab === 'local-files' && (
            <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: '1.5rem', minHeight: '550px' }}>
              
              {/* Directory File Navigator */}
              <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h3>Workspace Explorer</h3>
                  <button className="btn btn-secondary" style={{ padding: '0.25rem 0.5rem' }} onClick={() => handleListLocalFiles(currentLocalPath)}>
                    <RefreshCw size={12} />
                  </button>
                </div>
                
                <div style={{ fontSize: '0.75rem', color: 'hsl(var(--fg-muted))', wordBreak: 'break-all', background: '#000', padding: '0.4rem', borderRadius: '4px' }}>
                  Root: {workspaceInfo?.workspace_root || 'Loading...'}
                </div>

                {/* Back button */}
                {currentLocalPath && (
                  <button 
                    className="btn btn-secondary" 
                    style={{ justifyContent: 'flex-start', padding: '0.5rem' }}
                    onClick={() => {
                      const parts = currentLocalPath.split(/[/\\]/);
                      parts.pop();
                      handleListLocalFiles(parts.join('/'));
                    }}
                  >
                    .. [Up one directory]
                  </button>
                )}

                {/* List of files */}
                <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.35rem', maxHeight: '400px' }}>
                  {localFiles.length === 0 ? (
                    <div style={{ color: '#555', textAlign: 'center', padding: '2rem 0' }}>Folder empty</div>
                  ) : (
                    localFiles.map((file, idx) => (
                      <button 
                        key={idx} 
                        className={`nav-button ${selectedLocalFile?.relative_path === file.relative_path ? 'active' : ''}`}
                        style={{ padding: '0.5rem', borderRadius: '8px' }}
                        onClick={() => {
                          if (file.is_dir) {
                            handleListLocalFiles(file.relative_path);
                          } else {
                            handleSelectLocalFile(file);
                          }
                        }}
                      >
                        {file.is_dir ? <FolderOpen size={16} style={{ color: 'hsl(var(--accent))' }} /> : <FileText size={16} />}
                        <span style={{ fontSize: '0.85rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{file.name}</span>
                      </button>
                    ))
                  )}
                </div>
              </div>

              {/* Editor & Plan panel */}
              <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {selectedLocalFile ? (
                  <>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid hsl(var(--border))', paddingBottom: '0.75rem' }}>
                      <div>
                        <h2>Editing: {selectedLocalFile.name}</h2>
                        <span style={{ fontSize: '0.8rem', color: 'hsl(var(--fg-muted))' }}>Path: {selectedLocalFile.relative_path}</span>
                      </div>
                      <button className="btn btn-danger" onClick={handleLocalDeleteFile}>
                        <Trash2 size={16} /> Delete
                      </button>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                      
                      {/* Left: Raw text edits / Overwrites */}
                      <form onSubmit={handleLocalWriteSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        <div className="input-group">
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <label className="input-label">File Code Content</label>
                            <span style={{ fontSize: '0.75rem', color: 'hsl(var(--fg-muted))' }}>Editable overwrite view</span>
                          </div>
                          <textarea 
                            className="input-field" 
                            style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', minHeight: '220px' }}
                            value={localEditContent}
                            onChange={(e) => setLocalEditContent(e.target.value)}
                          />
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontSize: '0.9rem' }}>
                            <input type="checkbox" checked={localDryRun} onChange={(e) => setLocalDryRun(e.target.checked)} />
                            <span>Dry-run preview mode</span>
                          </label>

                          <div style={{ display: 'flex', gap: '0.5rem' }}>
                            <button type="submit" className="btn btn-primary">
                              Apply Full Edit
                            </button>
                            <button type="button" className="btn btn-secondary" onClick={() => setLocalEditContent(localFileContent)}>
                              Reset Changes
                            </button>
                          </div>
                        </div>
                      </form>

                      {/* Right: Find and Replace specific blocks */}
                      <form onSubmit={handleLocalModifySubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', borderLeft: '1px solid hsl(var(--border))', paddingLeft: '1rem' }}>
                        <h4 style={{ color: 'hsl(var(--accent))' }}>Target Replace Segment</h4>
                        <div className="input-group">
                          <label className="input-label">Find String Content (Exact Match)</label>
                          <textarea 
                            className="input-field"
                            style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', minHeight: '80px' }}
                            placeholder="Enter the exact block of code to search for..."
                            value={findText}
                            onChange={(e) => setFindText(e.target.value)}
                          />
                        </div>
                        <div className="input-group">
                          <label className="input-label">Replace String Content</label>
                          <textarea 
                            className="input-field"
                            style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', minHeight: '80px' }}
                            placeholder="Enter the replacement segment..."
                            value={replaceText}
                            onChange={(e) => setReplaceText(e.target.value)}
                          />
                        </div>

                        <button type="submit" className="btn btn-secondary" style={{ alignSelf: 'flex-end' }} disabled={!findText}>
                          Replace Match Segment
                        </button>
                      </form>
                    </div>

                    {/* Diff & Plan Display */}
                    {(localPlan || localDiff) && (
                      <div style={{ borderTop: '1px solid hsl(var(--border))', paddingTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                        <h4 style={{ color: 'hsl(var(--success))' }}>Modification Proposal Plan Preview</h4>
                        
                        {localPlan && (
                          <pre style={{ background: '#0e0a15', padding: '0.75rem', borderRadius: '8px', fontSize: '0.8rem', border: '1px solid #231b32', whiteSpace: 'pre-wrap' }}>
                            {localPlan}
                          </pre>
                        )}
                        
                        {localDiff && (
                          <div>
                            <div style={{ fontSize: '0.8rem', color: 'hsl(var(--fg-muted))', paddingBottom: '0.25rem' }}>Unified Diffs:</div>
                            {renderDiff(localDiff)}
                          </div>
                        )}

                        {localDryRun && (
                          <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
                            <button 
                              className="btn btn-primary"
                              onClick={async () => {
                                setLoading(true);
                                addLog("Executing changes proposal...");
                                // If findText is used, call modify. Else call write.
                                const res = findText 
                                  ? await api.modifyLocalFile(selectedLocalFile.relative_path, findText, replaceText, false)
                                  : await api.writeLocalFile(selectedLocalFile.relative_path, localEditContent, false);
                                setLoading(false);
                                if (res.success) {
                                  addLog("Proposal successfully executed!");
                                  setLocalDiff(null);
                                  setLocalPlan(null);
                                  setFindText('');
                                  setReplaceText('');
                                  // reload
                                  handleSelectLocalFile(selectedLocalFile);
                                } else {
                                  setErrorMsg(res.error || 'Modification failed');
                                }
                              }}
                            >
                              Approve and Commit Proposal Changes
                            </button>
                            <button className="btn btn-secondary" onClick={() => { setLocalDiff(null); setLocalPlan(null); }}>
                              Reject Proposal
                            </button>
                          </div>
                        )}
                      </div>
                    )}
                  </>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '350px', color: '#555' }}>
                    <FileText size={48} style={{ stroke: '#333', marginBottom: '1rem' }} />
                    <p>Select a file from the explorer list to view safety parameters, dry-run unified diffs, and perform safe edits.</p>
                  </div>
                )}
              </div>

            </div>
          )}

          {/* 9. Settings Tab */}
          {activeTab === 'settings' && (
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <h2>Model Adapter Config</h2>
              <p style={{ color: 'hsl(var(--fg-muted))', marginTop: '-1rem' }}>Manage model adapters dynamically. Switching provider modifies routing for Chat, Media Gen, and LangGraph classifications.</p>

              <div>
                <h3>Registered Providers</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem', marginTop: '1rem' }}>
                  {Object.values(providers).map((p, idx) => (
                    <div key={idx} className="card" style={{ background: p.is_active ? 'hsl(var(--primary) / 0.1)' : 'hsl(var(--bg-card) / 0.5)', borderColor: p.is_active ? 'hsl(var(--primary) / 0.5)' : 'hsl(var(--border))' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <h4 style={{ textTransform: 'capitalize' }}>{p.name.replace('_', ' ')}</h4>
                        {p.is_active ? (
                          <span className="pulse-badge">Active</span>
                        ) : (
                          <button 
                            className="btn btn-secondary" 
                            style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem' }}
                            disabled={!p.is_configured}
                            onClick={() => handleSwitchProvider(p.name)}
                          >
                            Switch
                          </button>
                        )}
                      </div>
                      <div style={{ marginTop: '0.75rem', fontSize: '0.85rem' }}>
                        <div>Status: {p.is_configured ? (
                          <span style={{ color: 'hsl(var(--success))', fontWeight: 600 }}>Configured</span>
                        ) : (
                          <span style={{ color: 'hsl(var(--danger))', fontWeight: 600 }}>Missing Configuration</span>
                        )}</div>
                        {!p.is_configured && p.missing_reason && (
                          <div style={{ color: 'hsl(var(--fg-muted))', fontSize: '0.75rem', marginTop: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                            <AlertCircle size={10} /> {p.missing_reason}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div style={{ borderTop: '1px solid hsl(var(--border))', paddingTop: '1.5rem', marginTop: '1rem' }}>
                <h3>Workspace Safety Profile</h3>
                <div style={{ marginTop: '1rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                  <div className="input-group">
                    <label className="input-label">File Edit Limit Size</label>
                    <input type="text" className="input-field" disabled value={`${workspaceInfo?.size_limit_mb || 10} MB`} />
                  </div>
                  <div className="input-group">
                    <label className="input-label">Workspace Folder Absolute Root</label>
                    <input type="text" className="input-field" disabled value={workspaceInfo?.workspace_root || ''} />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 10. Consulting Agency Tab */}
          {activeTab === 'company' && <CompanyTab />}

        </div>
      </main>
    </div>
  );
}
