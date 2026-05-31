import os
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List
from backend.app.company.models import Artifact
from backend.app.company.store import task_store
from backend.app.providers.manager import provider_manager

logger = logging.getLogger(__name__)

class BaseWorker(ABC):
    name: str
    description: str
    input_modalities: List[str]
    output_modalities: List[str]

    @abstractmethod
    async def execute(self, instruction: str, inputs: Dict[str, Any], task_id: str, step_id: str) -> List[Artifact]:
        """
        Runs the worker capability.
        - inputs: dictionary of resolved input values/artifacts
        Returns a list of Artifact models representing outputs.
        """
        pass

class WorkerRegistry:
    def __init__(self):
        self._workers: Dict[str, BaseWorker] = {}

    def register(self, worker: BaseWorker) -> None:
        logger.info(f"Registering worker capability: '{worker.name}'")
        self._workers[worker.name] = worker

    def get_worker(self, name: str) -> BaseWorker:
        if name not in self._workers:
            raise ValueError(f"Worker capability '{name}' is not registered.")
        return self._workers[name]

    def list_workers(self) -> List[BaseWorker]:
        return list(self._workers.values())

    def get_supervisor_prompt_context(self) -> str:
        """Dynamically builds prompt instructions of registered workers for the Supervisor."""
        context = "Available Workers for assignment:\n"
        for w in self.list_workers():
            context += f"- name: '{w.name}'\n"
            context += f"  description: {w.description}\n"
            context += f"  inputs required: {w.input_modalities}\n"
            context += f"  outputs produced: {w.output_modalities}\n\n"
        return context

# Instantiate global registry singleton
worker_registry = WorkerRegistry()


# --- Worker Implementations ---

class TextWorker(BaseWorker):
    name = "text_worker"
    description = "Generates text content, analyses, marketing copies, slogans, reports, summaries, or plans."
    input_modalities = ["text"]
    output_modalities = ["text"]

    async def execute(self, instruction: str, inputs: Dict[str, Any], task_id: str, step_id: str) -> List[Artifact]:
        logger.info(f"Executing TextWorker for step {step_id}")
        
        # Build prompt from input refs context if available
        context_str = ""
        if inputs:
            context_str = "Context from previous steps:\n"
            for k, v in inputs.items():
                context_str += f"- {k}: {v}\n"
            context_str += "\n"
            
        prompt = (
            f"{context_str}"
            f"Instruction: {instruction}\n"
            "Please generate the required text content based on the instruction and context above."
        )
        
        provider = provider_manager.active_provider
        resp = await provider.chat([
            {"role": "system", "content": "You are a specialized worker agent representing an AI Consulting Company. Produce detailed, high-quality, professional results."},
            {"role": "user", "content": prompt}
        ])
        
        if not resp["success"]:
            raise RuntimeError(f"TextWorker model provider failure: {resp['error']}")
            
        choices = resp["data"].get("choices", [])
        content = ""
        if choices:
            content = choices[0].get("message", {}).get("content", "")
        elif "reply" in resp["data"]:
            content = resp["data"]["reply"]
            
        # Save artifact file
        artifacts_dir = task_store.get_artifacts_dir(task_id)
        filename = f"{step_id}_text.txt"
        filepath = artifacts_dir.joinpath(filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
            
        # Convert path to relative workspace path for portable storage
        rel_path = f"tasks/{task_id}/artifacts/{filename}"
        
        artifact = Artifact(
            artifact_id=f"artifact_{step_id}_text_0",
            type="text",
            path_or_url=rel_path,
            source_step_id=step_id,
            metadata={"character_count": len(content)}
        )
        
        return [artifact]

# Register
worker_registry.register(TextWorker())


class TextToImageWorker(BaseWorker):
    name = "image_gen_worker"
    description = "Generates new logos, pictures, drawings, designs, or banners from a text prompt description."
    input_modalities = ["text"]
    output_modalities = ["image"]

    async def execute(self, instruction: str, inputs: Dict[str, Any], task_id: str, step_id: str) -> List[Artifact]:
        logger.info(f"Executing TextToImageWorker for step {step_id}")
        
        # Determine prompt
        prompt = instruction
        if "prompt" in inputs:
            prompt = inputs["prompt"]
        elif inputs:
            # Fallback join
            prompt = f"{instruction}. Context: " + ", ".join(f"{k}: {v}" for k, v in inputs.items())

        enable_mock = os.environ.get("ENABLE_MOCK_IMAGE_PROVIDER", "false").lower() == "true"
        artifacts_dir = task_store.get_artifacts_dir(task_id)
        
        if enable_mock:
            logger.info("Mock Image Provider enabled. Creating local SVG placeholder.")
            filename = f"{step_id}_image.svg"
            filepath = artifacts_dir.joinpath(filename)
            
            # Draw gradient SVG
            svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#a855f7;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#06b6d4;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="100%" height="100%" fill="url(#grad)" rx="20"/>
  <circle cx="256" cy="200" r="90" fill="white" fill-opacity="0.15" />
  <path d="M256 130 L320 270 L192 270 Z" fill="white" fill-opacity="0.8" />
  <text x="50%" y="340" font-family="'Outfit', sans-serif" font-size="28" font-weight="bold" fill="white" text-anchor="middle">DB AI Consulting</text>
  <text x="50%" y="390" font-family="'Outfit', sans-serif" font-size="16" fill="white" fill-opacity="0.8" text-anchor="middle">Prompt: {prompt[:40]}</text>
  <text x="50%" y="430" font-family="'Outfit', sans-serif" font-size="12" fill="white" fill-opacity="0.5" text-anchor="middle">[ MOCK IMAGE ARTIFACT: {step_id} ]</text>
</svg>"""
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(svg_content)
                
            rel_path = f"tasks/{task_id}/artifacts/{filename}"
            return [Artifact(
                artifact_id=f"artifact_{step_id}_image_0",
                type="image",
                path_or_url=rel_path,
                source_step_id=step_id,
                metadata={"mock": True, "prompt": prompt}
            )]
        else:
            provider = provider_manager.active_provider
            resp = await provider.generate_image(prompt)
            if not resp["success"]:
                raise RuntimeError(f"ImageGenWorker model provider failure: {resp['error']}")
                
            # MiniMax formats
            url = resp["data"].get("images", [{}])[0].get("url") or resp["data"].get("data", {}).get("image_urls", [None])[0] or resp["data"].get("url")
            if not url:
                raise RuntimeError(f"ImageGenWorker failed: no image URL returned in provider response.")
                
            return [Artifact(
                artifact_id=f"artifact_{step_id}_image_0",
                type="image",
                path_or_url=url,
                source_step_id=step_id,
                metadata={"mock": False, "prompt": prompt}
            )]

# Register
worker_registry.register(TextToImageWorker())


class ImageEditWorker(BaseWorker):
    name = "image_edit_worker"
    description = "Edits, filters, refines, or alters a base logo/picture/design utilizing detailed textual suggestions."
    input_modalities = ["text", "image"]
    output_modalities = ["image"]

    async def execute(self, instruction: str, inputs: Dict[str, Any], task_id: str, step_id: str) -> List[Artifact]:
        logger.info(f"Executing ImageEditWorker for step {step_id}")
        
        prompt = instruction
        if "prompt" in inputs:
            prompt = inputs["prompt"]
            
        base_image = ""
        base_image_ref = "none"
        if "base_image" in inputs:
            base_image = inputs["base_image"]
            base_image_ref = base_image.split("/")[-1] if "/" in base_image else base_image
            
        enable_mock = os.environ.get("ENABLE_MOCK_IMAGE_PROVIDER", "false").lower() == "true"
        artifacts_dir = task_store.get_artifacts_dir(task_id)
        
        if enable_mock:
            logger.info("Mock Image Provider enabled. Creating local SVG edit mockup.")
            filename = f"{step_id}_edit.svg"
            filepath = artifacts_dir.joinpath(filename)
            
            # Draw edit SVG
            svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#3b82f6;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#ec4899;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="100%" height="100%" fill="url(#grad)" rx="20"/>
  <rect x="128" y="100" width="256" height="180" rx="10" fill="white" fill-opacity="0.1" stroke="white" stroke-width="2" stroke-dasharray="5,5" />
  <text x="50%" y="190" font-family="'Outfit', sans-serif" font-size="16" fill="white" font-weight="bold" text-anchor="middle">Base Layer: {base_image_ref[:20]}</text>
  <text x="50%" y="330" font-family="'Outfit', sans-serif" font-size="24" font-weight="bold" fill="white" text-anchor="middle">Edit Layer Applied</text>
  <text x="50%" y="380" font-family="'Outfit', sans-serif" font-size="16" fill="white" fill-opacity="0.8" text-anchor="middle">Edit Prompt: {prompt[:40]}</text>
  <text x="50%" y="420" font-family="'Outfit', sans-serif" font-size="12" fill="white" fill-opacity="0.5" text-anchor="middle">[ MOCK EDIT ARTIFACT: {step_id} ]</text>
</svg>"""
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(svg_content)
                
            rel_path = f"tasks/{task_id}/artifacts/{filename}"
            return [Artifact(
                artifact_id=f"artifact_{step_id}_image_0",
                type="image",
                path_or_url=rel_path,
                source_step_id=step_id,
                metadata={"mock": True, "operation": "image_edit", "base_image": base_image, "prompt": prompt}
            )]
        else:
            provider = provider_manager.active_provider
            
            # Retrieve base image bytes or URL. If it's a relative local path, load bytes.
            # For simplicity, we fetch it or raise a worker error if path cannot be loaded.
            image_data = b""
            if base_image and not base_image.startswith("http"):
                local_full_path = task_store.workspace_root.joinpath(base_image)
                if local_full_path.exists():
                    with open(local_full_path, "rb") as f:
                        image_data = f.read()
                else:
                    raise FileNotFoundError(f"Base image file not found at: {base_image}")
            else:
                raise ValueError("ImageEditWorker requires a valid local base image path in this MVP.")
                
            resp = await provider.image_to_image(image_data, prompt)
            if not resp["success"]:
                raise RuntimeError(f"ImageEditWorker model provider failure: {resp['error']}")
                
            url = resp["data"].get("images", [{}])[0].get("url") or resp["data"].get("data", {}).get("image_urls", [None])[0] or resp["data"].get("url")
            if not url:
                raise RuntimeError("ImageEditWorker failed: no image URL returned in provider response.")
                
            return [Artifact(
                artifact_id=f"artifact_{step_id}_image_0",
                type="image",
                path_or_url=url,
                source_step_id=step_id,
                metadata={"mock": False, "operation": "image_edit", "base_image": base_image, "prompt": prompt}
            )]

# Register
worker_registry.register(ImageEditWorker())
