-- Enhanced Data Structure for Article Intelligence System
-- With detailed website information and AI classification

-- Main articles table with comprehensive website metadata
CREATE TABLE IF NOT EXISTS articles_v2 (
    -- Core Identifiers
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    url TEXT NOT NULL,
    url_hash TEXT UNIQUE,
    
    -- Website Information
    domain TEXT,                    -- e.g., 'github.com'
    subdomain TEXT,                  -- e.g., 'blog', 'news', 'docs'
    path_segments TEXT,              -- JSON array of URL path parts
    protocol TEXT,                   -- http/https
    port INTEGER,                    -- port number if specified
    query_params TEXT,               -- JSON object of query parameters
    
    -- Content Metadata
    title TEXT,
    meta_description TEXT,           -- from meta tags
    meta_keywords TEXT,              -- from meta keywords
    og_title TEXT,                   -- Open Graph title
    og_description TEXT,             -- Open Graph description
    og_image TEXT,                   -- Open Graph image URL
    og_type TEXT,                    -- article/website/blog
    canonical_url TEXT,              -- canonical URL if different
    
    -- Content Body
    content TEXT,                    -- main article text
    content_html TEXT,               -- original HTML structure
    extracted_images TEXT,           -- JSON array of image URLs
    extracted_links TEXT,            -- JSON array of external links
    extracted_videos TEXT,           -- JSON array of video URLs
    
    -- AI Analysis - Classification
    category TEXT,                   -- main category
    subcategory TEXT,                -- detailed subcategory
    industry TEXT,                   -- industry/sector
    topics TEXT,                     -- JSON array of topics
    tags TEXT,                       -- JSON array of tags
    keywords TEXT,                   -- JSON array of extracted keywords
    
    -- AI Analysis - Entities
    people TEXT,                     -- JSON array with roles
    organizations TEXT,              -- JSON array with types
    locations TEXT,                  -- JSON array with geo data
    technologies TEXT,               -- JSON array with versions
    products TEXT,                   -- JSON array of products mentioned
    events TEXT,                     -- JSON array of events
    dates_mentioned TEXT,            -- JSON array of important dates
    
    -- AI Analysis - Content Quality
    summary TEXT,                    -- AI-generated summary
    summary_bullet_points TEXT,      -- JSON array of bullet points
    sentiment TEXT,                  -- positive/negative/neutral
    sentiment_score REAL,            -- -1 to 1
    mood TEXT,                       -- informative/urgent/casual/technical
    complexity_level TEXT,           -- beginner/intermediate/advanced
    readability_score REAL,          -- Flesch reading ease
    
    -- AI Analysis - Insights
    key_points TEXT,                 -- JSON array of main points
    action_items TEXT,               -- JSON array of actionable items
    questions_raised TEXT,           -- JSON array of questions
    predictions TEXT,                -- JSON array of predictions made
    claims TEXT,                     -- JSON array of claims to verify
    
    -- Website Technical Info
    website_type TEXT,               -- news/blog/docs/social/forum/ecommerce
    cms_detected TEXT,               -- WordPress/Medium/Ghost/custom
    ssl_enabled BOOLEAN,             -- HTTPS availability
    response_time_ms INTEGER,        -- page load time
    page_size_kb INTEGER,            -- total page size
    
    -- Source Credibility
    source_credibility TEXT,         -- high/medium/low
    source_type TEXT,                -- news/blog/research/social/documentation
    author TEXT,                     -- article author
    author_bio TEXT,                 -- author description
    author_social TEXT,              -- JSON of author social links
    
    -- Publication Info
    published_date TIMESTAMP,        -- when article was published
    modified_date TIMESTAMP,         -- last modification date
    language TEXT,                   -- detected language
    language_confidence REAL,        -- language detection confidence
    
    -- Engagement Metrics
    social_shares TEXT,              -- JSON of share counts by platform
    comments_count INTEGER,          -- number of comments if available
    likes_count INTEGER,             -- likes/upvotes if available
    
    -- Content Metrics
    word_count INTEGER,              -- total words
    sentence_count INTEGER,          -- total sentences
    paragraph_count INTEGER,         -- total paragraphs
    reading_time INTEGER,            -- estimated minutes
    unique_words INTEGER,            -- vocabulary diversity
    
    -- User Interaction
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP,
    access_count INTEGER DEFAULT 1,
    is_read BOOLEAN DEFAULT 0,
    is_archived BOOLEAN DEFAULT 0,
    is_favorite BOOLEAN DEFAULT 0,
    user_notes TEXT,
    user_rating INTEGER,            -- 1-5 stars
    user_tags TEXT,                 -- JSON array of user-added tags
    
    -- Relationships
    related_articles TEXT,           -- JSON array of related article IDs
    referenced_by TEXT,              -- JSON array of articles referencing this
    follow_up_reminder TIMESTAMP,
    
    -- Processing Status
    ai_processed BOOLEAN DEFAULT 0,
    ai_processed_at TIMESTAMP,
    extraction_errors TEXT,          -- JSON of any extraction errors
    processing_version TEXT,         -- version of processing algorithm
    
    -- Indexes for performance
    INDEX idx_domain ON articles_v2(domain),
    INDEX idx_category ON articles_v2(category, subcategory),
    INDEX idx_published ON articles_v2(published_date),
    INDEX idx_user_saved ON articles_v2(user_id, saved_at),
    INDEX idx_credibility ON articles_v2(source_credibility)
);

-- Website profiles table for domain-level insights
CREATE TABLE IF NOT EXISTS website_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain TEXT UNIQUE,
    
    -- Website Classification
    primary_category TEXT,           -- main content category
    website_type TEXT,               -- news/blog/corporate/ecommerce
    industry TEXT,                   -- industry sector
    target_audience TEXT,            -- audience description
    
    -- Technical Profile
    cms_platform TEXT,               -- detected CMS
    technology_stack TEXT,           -- JSON array of detected tech
    ssl_certificate TEXT,            -- certificate details
    server_location TEXT,            -- geographic location
    cdn_provider TEXT,               -- CDN if detected
    
    -- Content Profile
    primary_language TEXT,           -- main language
    content_frequency TEXT,          -- daily/weekly/monthly
    average_article_length INTEGER,  -- average words
    common_topics TEXT,              -- JSON array of frequent topics
    writing_style TEXT,              -- formal/casual/technical
    
    -- Credibility Metrics
    domain_age_days INTEGER,         -- age of domain
    alexa_rank INTEGER,              -- traffic rank
    trust_score REAL,                -- 0-100 trust score
    fact_checking_record TEXT,       -- JSON of fact-check results
    bias_rating TEXT,                -- left/center/right/neutral
    
    -- Engagement Metrics
    avg_social_shares INTEGER,       -- average shares per article
    avg_comments INTEGER,            -- average comments
    user_engagement_score REAL,      -- calculated engagement score
    
    -- Metadata
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP,
    total_articles_saved INTEGER DEFAULT 0,
    
    INDEX idx_website_domain ON website_profiles(domain)
);

-- Content patterns table for learning
CREATE TABLE IF NOT EXISTS content_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_type TEXT,               -- topic_trend/sentiment_shift/author_style
    pattern_name TEXT,
    pattern_data TEXT,               -- JSON of pattern details
    
    -- Pattern Metrics
    occurrences INTEGER,             -- times pattern observed
    confidence_score REAL,           -- pattern confidence 0-1
    first_observed TIMESTAMP,
    last_observed TIMESTAMP,
    
    -- Related Content
    example_articles TEXT,           -- JSON array of article IDs
    related_domains TEXT,            -- JSON array of domains
    
    INDEX idx_pattern_type ON content_patterns(pattern_type)
);

-- Time series data for trending
CREATE TABLE IF NOT EXISTS article_timeseries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER,
    metric_date DATE,
    
    -- Daily Metrics
    views_count INTEGER DEFAULT 0,
    shares_count INTEGER DEFAULT 0,
    sentiment_score REAL,
    relevance_score REAL,
    
    FOREIGN KEY (article_id) REFERENCES articles_v2(id),
    INDEX idx_timeseries ON article_timeseries(article_id, metric_date)
);

-- Category taxonomy table
CREATE TABLE IF NOT EXISTS category_taxonomy (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    subcategory TEXT,
    description TEXT,
    keywords TEXT,                   -- JSON array of associated keywords
    parent_category_id INTEGER,
    
    INDEX idx_taxonomy ON category_taxonomy(category, subcategory)
);

-- Create views for easy data access

-- View for latest articles with key info
CREATE VIEW IF NOT EXISTS v_latest_articles AS
SELECT 
    id,
    domain,
    title,
    category,
    subcategory,
    summary,
    sentiment,
    source_credibility,
    published_date,
    saved_at,
    reading_time,
    word_count
FROM articles_v2
ORDER BY saved_at DESC
LIMIT 100;

-- View for website statistics
CREATE VIEW IF NOT EXISTS v_website_stats AS
SELECT 
    domain,
    website_type,
    COUNT(*) as article_count,
    AVG(word_count) as avg_words,
    AVG(reading_time) as avg_reading_time,
    AVG(sentiment_score) as avg_sentiment,
    MAX(saved_at) as last_saved
FROM articles_v2
GROUP BY domain, website_type;

-- View for trending topics
CREATE VIEW IF NOT EXISTS v_trending_topics AS
SELECT 
    topics,
    COUNT(*) as mention_count,
    AVG(sentiment_score) as avg_sentiment,
    MAX(saved_at) as last_mentioned
FROM articles_v2
WHERE saved_at > datetime('now', '-7 days')
GROUP BY topics
ORDER BY mention_count DESC;