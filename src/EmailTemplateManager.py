from pathlib import Path


class EmailTemplateManager:
    """Manages HTML email templates and rendering."""

    def __init__(self):
        self.template_dir = Path(__file__).parent / "templates"
        self.css_content = self._load_css()
        self.main_template = self._load_template("email.html")
        self.competition_card_template = self._load_template(
            "competition.html")
        self.no_competitions_template = self._load_template(
            "no_competitions.html")
        self.summary_stats_template = self._load_template("summary.html")

    def _load_css(self):
        """Load CSS content from file."""
        css_file = self.template_dir / "template.css"
        if css_file.exists():
            return css_file.read_text(encoding='utf-8')
        return ""

    def _load_template(self, filename):
        """Load HTML template from file."""
        template_file = self.template_dir / filename
        if template_file.exists():
            return template_file.read_text(encoding='utf-8')
        return ""

    def render_competition_card(self, name, host, distance, details_html):
        """Render a single competition card."""
        return self.competition_card_template.format(
            name=name,
            host=host,
            distance=distance,
            competition_details=details_html
        )

    def render_summary_stats(self, competitions_df):
        """Render the summary statistics section."""
        if competitions_df is None or len(competitions_df) == 0:
            return ""

        distances = competitions_df['distance_miles'].dropna()
        if len(distances) == 0:
            return ""

        return self.summary_stats_template.format(
            total_count=len(competitions_df),
            closest_distance=distances.min(),
            furthest_distance=distances.max(),
            average_distance=distances.mean()
        )

    def render_detail_row(self, icon, label, value, link=None):
        """Render a detail row within a competition card."""
        if link:
            value_html = f'<a href="{link}" style="color: #667eea; text-decoration: none;">{value}</a>'
        else:
            value_html = str(value)

        return f'''
        <div class="detail-row">
            <span class="detail-label icon">{icon}</span>
            <span class="detail-value">{value_html}</span>
        </div>
        '''

    def render_no_competitions(self):
        """Render the no competitions found section."""
        return self.no_competitions_template

    def render_full_email(self, user_name, postcode, max_distance, competitions_content, current_date):
        """Render the complete email HTML."""
        return self.main_template.format(
            css_styles=self.css_content,
            user_name=user_name,
            postcode=postcode,
            max_distance=max_distance,
            competitions_content=competitions_content,
            current_date=current_date
        )
