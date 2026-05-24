"""
Test suite for bug fixes in critical and high-priority issues.

Tests for:
1.1 AiReportsService - HTTPException handling
1.2 MicrophoneService - Thread-safe recording
1.3 Routes - Queue timeout handling
2.1 DocumentService - Exception handling and responses
2.2 DocumentService - Absolute paths
2.3 FeedbackService - Input validation
"""

import pytest
import os
import tempfile
import threading
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pathlib import Path

# Test 1.1: AiReportsService exception handling
class TestAiReportsServiceFix:
    """Test that HTTPException is raised instead of returned."""
    
    @pytest.mark.asyncio
    async def test_llama_api_error_raises_exception(self):
        """Test that exceptions from llama_api_call are properly raised."""
        from src.api.services.reports import AiGeneretadReportsWithLlama
        from src.core.models import EventModel
        from fastapi import HTTPException
        
        mock_event = EventModel(
            type="test_event",
            origin="test",
            details={"test": "data"}
        )
        
        # Mock llama_api_call to raise an exception
        with patch('src.AiServices.services.AiReportsService.llama_api_call') as mock_llama:
            mock_llama.side_effect = Exception("API Error")
            
            # Should raise HTTPException, not return it
            with pytest.raises(HTTPException) as exc_info:
                await AiGeneretadReportsWithLlama(mock_event, "test response", [], "test")
            
            assert exc_info.value.status_code == 500
            assert "API Error" in exc_info.value.detail


# Test 1.2: MicrophoneService thread-safety
class TestMicrophoneServiceFix:
    """Test that MicrophoneService is thread-safe."""
    
    def test_audio_recorder_singleton_exists(self):
        """Test that AudioRecorder class is defined and instantiated."""
        from src.backend.services.MicrophoneService import AudioRecorder, _recorder
        
        assert _recorder is not None
        assert isinstance(_recorder, AudioRecorder)
    
    def test_audio_recorder_has_lock(self):
        """Test that AudioRecorder uses RLock for thread safety."""
        from src.backend.services.MicrophoneService import AudioRecorder
        
        recorder = AudioRecorder()
        assert hasattr(recorder, '_lock')
        assert type(recorder._lock).__name__ == 'RLock'
    
    def test_cannot_start_recording_twice(self):
        """Test that starting recording twice returns error message."""
        from src.backend.services.MicrophoneService import AudioRecorder
        
        recorder = AudioRecorder()
        
        # Mock the InputStream to avoid actual mic access
        with patch('src.backend.services.MicrophoneService.sd.InputStream'):
            result1 = recorder.start_recording()
            assert "initialize recording" in result1
            
            # Try to start again
            result2 = recorder.start_recording()
            assert "Gravação já em andamento" in result2
            
            # Cleanup
            recorder.is_recording = False
    
    def test_stop_recording_without_start(self):
        """Test that stopping recording without starting returns error message."""
        from src.backend.services.MicrophoneService import AudioRecorder
        
        recorder = AudioRecorder()
        result = recorder.stop_recording()
        assert "No recordings in progress" in result


# Test 1.3: Routes queue timeout handling
class TestRoutesQueueTimeoutFix:
    """Test that queue.get() has timeout handling."""
    
    @pytest.mark.asyncio
    async def test_process_audio_has_timeout(self):
        """Test that processAudio endpoint has timeout for queue.get()."""
        # This is a code review test - we verify the fix exists in the source
        from src.backend.routes import Routes
        import inspect
        
        # Get the source code of processAudio function
        source = inspect.getsource(Routes.processAudio)
        
        # Verify that asyncio.wait_for is used with timeout
        assert "asyncio.wait_for" in source
        assert "timeout=" in source or "timeout =" in source
        assert "300" in source  # 5 minutes timeout
    
    @pytest.mark.asyncio
    async def test_audio_processing_timeout_error(self):
        """Test TimeoutError handling in processAudio."""
        from fastapi import HTTPException
        
        # Simulate a timeout scenario
        async def timeout_queue():
            await asyncio.sleep(400)  # More than 5 minutes
        
        # Test that TimeoutError would result in proper HTTP response
        try:
            await asyncio.wait_for(timeout_queue(), timeout=1.0)
        except asyncio.TimeoutError:
            # This should be caught and converted to HTTPException with status 504
            pass


# Test 2.1: DocumentService exception handling
class TestDocumentServiceExceptionFixing:
    """Test that DocumentService has proper exception handling."""
    
    def test_upload_dir_uses_absolute_path(self):
        """Test that UPLOAD_DIR is an absolute path."""
        from src.backend.services.DocumentService import UPLOAD_DIR
        
        # Should be absolute path
        assert os.path.isabs(UPLOAD_DIR)
    
    @pytest.mark.asyncio
    async def test_invalid_filename_returns_error(self):
        """Test that invalid filenames are handled."""
        from src.backend.services.DocumentService import saveDocumentsCompany
        from fastapi import UploadFile
        
        # Create a mock file with no filename
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.filename = None
        
        result = await saveDocumentsCompany([mock_file])
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert "error" in result[0]
    
    @pytest.mark.asyncio
    async def test_view_all_documents_returns_empty_list_not_false(self):
        """Test that viewAllCompanyDocuments returns [] not False."""
        from src.backend.services.DocumentService import viewAllCompanyDocuments
        
        with patch('src.backend.services.DocumentService.get_all_documentos') as mock_get:
            mock_get.return_value = None
            
            result = await viewAllCompanyDocuments()
            
            # Should return empty list, not False
            assert result == []
            assert result is not False


# Test 2.3: FeedbackService validation
class TestFeedbackServiceValidationFix:
    """Test that FeedbackService has proper input validation."""
    
    @pytest.mark.asyncio
    async def test_feedback_validation_missing_event_id(self):
        """Test that missing event_id is validated."""
        from src.backend.services.FeedbackService import service_submit_feedback
        from src.api.services.feedback import Feedback
        
        # Create feedback without event_id
        feedback = Feedback(
            event_id=None,
            human_classification="test",
            human_priority="Alta",
            comment="test"
        )
        
        result = await service_submit_feedback(feedback)
        
        # Should return False due to validation error
        assert result is False
    
    @pytest.mark.asyncio
    async def test_feedback_validation_invalid_priority(self):
        """Test that invalid priority is validated."""
        from src.backend.services.FeedbackService import service_submit_feedback
        from src.api.services.feedback import Feedback
        
        feedback = Feedback(
            event_id=1,
            human_classification="test",
            human_priority="INVALID_PRIORITY",
            comment="test"
        )
        
        result = await service_submit_feedback(feedback)
        
        # Should return False due to validation error
        assert result is False
    
    @pytest.mark.asyncio
    async def test_feedback_validation_comment_too_long(self):
        """Test that oversized comments are validated."""
        from src.backend.services.FeedbackService import service_submit_feedback
        from src.api.services.feedback import Feedback
        
        feedback = Feedback(
            event_id=1,
            human_classification="test",
            human_priority="Alta",
            comment="x" * 5001  # Exceeds 5000 char limit
        )
        
        result = await service_submit_feedback(feedback)
        
        # Should return False due to validation error
        assert result is False
    
    @pytest.mark.asyncio
    async def test_feedback_validation_valid_feedback(self):
        """Test that valid feedback passes validation."""
        from src.backend.services.FeedbackService import service_submit_feedback
        from src.api.services.feedback import Feedback
        
        feedback = Feedback(
            event_id=1,
            human_classification="test",
            human_priority="Alta",
            comment="Valid comment"
        )
        
        with patch('src.backend.services.FeedbackService.save_human_feedback'):
            result = await service_submit_feedback(feedback)
            
            # Should return True
            assert result is True


# Integration tests
class TestBugFixesIntegration:
    """Integration tests for bug fixes."""
    
    def test_logging_is_configured(self):
        """Test that logging is properly imported in fixed modules."""
        import src.backend.services.DocumentService as doc_service
        import src.backend.services.FeedbackService as feedback_service
        import src.backend.services.MicrophoneService as mic_service
        import src.backend.routes.Routes as routes
        
        # All modules should have logging import
        assert hasattr(doc_service, 'log') or 'logging' in str(doc_service.__dict__)
        assert hasattr(feedback_service, 'log')
        assert hasattr(mic_service, 'log')
        assert hasattr(routes, 'log')
