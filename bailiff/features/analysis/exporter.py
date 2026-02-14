from bailiff.features.memory.models import Sessions
from typing import Tuple
import logging
import os

from bailiff.core.db import SessionLocal
from bailiff.features.memory.storage import MeetingStorage
from bailiff.features.analysis.digestion import Digester

from bailiff.features.analysis.summarization import Summarizer

logger = logging.getLogger("bailiff.features.analysis.exporter")

# FIXME: bug with empty transcription crashes the export

class Exporter:
    """
    Handles the export of meeting data including raw transcripts, digested transcripts, and summaries.

    This class coordinates the retrieval of data from storage and the execution of digestion and 
    summarization processes to generate markdown files for the user.
    """
    
    def __init__(self, session_id: int, output_path: str, storage: MeetingStorage, digester: Digester = None, summarizer: Summarizer = None):
        self.session_id = session_id
        self.storage = storage
        self.output_path = output_path
        self.digester = digester
        self.summarizer = summarizer

    def _get_session_details(self) -> Tuple[Sessions, str]:
        """
        Returns the session and the session name.
        """
        session = self.storage.get_session(self.session_id)
        if not session:
            logger.error(f"Session {self.session_id} not found!")
            raise ValueError(f"Session {self.session_id} not found!")
        
        clean_name = "".join(c for c in session.name if c.isalnum() or c in (' ', '_')).rstrip()
        session_name = clean_name.replace(" ", "_")

        return session, session_name

    def raw_export(self):
        """
        Exports the raw transcript to a markdown file.
        """
        logger.info(f"Exporting session {self.session_id} to {self.output_path}")
        
        session, session_name = self._get_session_details()
        transcripts = self.storage.get_transcripts(self.session_id)
        
        filename = os.path.join(self.output_path, "raw", f"{session_name}.md")

        output_dir = os.path.dirname(filename)
        os.makedirs(output_dir, exist_ok=True)
        
        content = [
            f"# {session.name}\n",
            f"## {session.start_time}\n\n"
        ]

        for transcript in transcripts:
            content.append(f"**{transcript.speaker}**: {transcript.text}\n\n")
        
        
        with open(filename, "w", encoding="utf-8") as file:
            logger.debug(f"Writing session {self.session_id} to {filename} ({len(content)} lines)")
            file.writelines(content)
        
        logger.info(f"Exported session {self.session_id} to {filename}")
        return filename

    def digest_export(self):
        """
        Exports the digested transcript to a markdown file.
        """
        if not self.digester:
            raise ValueError("Digester instance is required for digest export")

        logger.info(f"Exporting digest for session {self.session_id} to {self.output_path}")
        
        _, session_name = self._get_session_details()
        filename = os.path.join(self.output_path, "digest", f"{session_name}.md")

        output_dir = os.path.dirname(filename)
        os.makedirs(output_dir, exist_ok=True)
        
        digest = self.digester.digest(self.session_id)
        
        with open(filename, "w", encoding="utf-8") as file:
            logger.debug(f"Writing session {self.session_id} to {filename} ({len(digest)} lines)")
            file.write(digest)
        
        logger.info(f"Exported digest for session {self.session_id} to {filename}")
        return filename

    def summary_export(self):
        """
        Exports the summary to a markdown file.
        """
        if not self.summarizer:
            raise ValueError("Summarizer instance is required for summary export")

        logger.info(f"Exporting summary for session {self.session_id} to {self.output_path}")

        _, session_name = self._get_session_details()
        
        # Check if a digest file exists
        digest_filename = os.path.join(self.output_path, "digest", f"{session_name}.md")
        if not os.path.exists(digest_filename):
            logger.info(f"Digest file {digest_filename} not found! Exporting digest...")
            # Ensure we have digester if we need to run it
            if not self.digester:
                 raise ValueError("Digester instance is required for summary export when digest is missing")
            self.digest_export()
        else:
            logger.info(f"Digest file {digest_filename} found! Using existing digest.")
        
        with open(digest_filename, "r", encoding="utf-8") as file:
            digest = file.read()
        
        # Export summary
        summary_filename = os.path.join(self.output_path, "summary", f"{session_name}.md")
        output_dir = os.path.dirname(summary_filename)
        os.makedirs(output_dir, exist_ok=True)
        
        summary = self.summarizer.summarize(digest)
        
        with open(summary_filename, "w", encoding="utf-8") as file:
            logger.debug(f"Writing session {self.session_id} to {summary_filename} ({len(summary)} lines)")
            file.write(summary)
        
        logger.info(f"Exported summary for session {self.session_id} to {summary_filename}")
        return summary_filename

    def full_export(self):
        """
        Exports the raw transcript, the digested transcript and the summary to markdown files.
        """
        raw_file = self.raw_export()
        digest_file = self.digest_export()
        summary_file = self.summary_export()
        return raw_file, digest_file, summary_file
        
        