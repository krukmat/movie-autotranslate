from workers.pipeline import tasks
from shared.models import JobStage


def test_parse_resume_defaults_to_asr() -> None:
    assert tasks._parse_resume(None) == JobStage.ASR
    assert tasks._parse_resume("UNKNOWN") == JobStage.ASR
    assert tasks._parse_resume(JobStage.TTS.value) == JobStage.TTS


def test_should_skip_stage_only_when_artifacts_ready() -> None:
    resume_stage = JobStage.TTS
    assert tasks._should_skip(JobStage.ASR, resume_stage, artifact_ready=True) is True
    assert tasks._should_skip(JobStage.ASR, resume_stage, artifact_ready=False) is False
    assert tasks._should_skip(JobStage.TTS, resume_stage, artifact_ready=True) is False
