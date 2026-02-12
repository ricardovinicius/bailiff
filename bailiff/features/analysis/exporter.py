import logging
from bailiff.core.db import SessionLocal
from bailiff.features.memory.storage import MeetingStorage

logger = logging.getLogger("bailiff.features.analysis.exporter")

class Exporter:
    def __init__(self, session_id: int, output_path: str, storage: MeetingStorage):
        self.session_id = session_id
        self.storage = storage
        self.output_path = output_path

    def raw_export(self):
        logger.info(f"Exporting session {self.session_id} to {self.output_path}")
        
        session = self.storage.get_session(self.session_id)
        if not session:
            logger.error(f"Session {self.session_id} not found!")
            raise ValueError(f"Session {self.session_id} not found!")
        
        transcripts = self.storage.get_transcripts(self.session_id)
        
        # Ensure output directory exists
        import os
        
        clean_name = "".join(c for c in session.name if c.isalnum() or c in (' ', '_')).rstrip()
        session_name = clean_name.replace(" ", "_")
        filename = os.path.join(self.output_path, f"{session_name}.md")

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

        