def create_article_saved_flex(article_info, row_number):
    return {
        "type": "bubble",
        "size": "kilo",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": "✅ Article Saved",
                            "color": "#ffffff",
                            "size": "lg",
                            "weight": "bold",
                            "flex": 1
                        },
                        {
                            "type": "text",
                            "text": f"Row #{row_number}",
                            "color": "#ffffff",
                            "size": "sm",
                            "align": "end"
                        }
                    ]
                }
            ],
            "backgroundColor": "#27ACB2",
            "paddingAll": "20px"
        },
        "hero": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": article_info.get('category', 'General'),
                            "size": "xs",
                            "color": "#ffffff",
                            "weight": "bold"
                        }
                    ],
                    "backgroundColor": get_category_color(article_info.get('category', 'General')),
                    "paddingAll": "8px",
                    "cornerRadius": "4px",
                    "width": "100px"
                },
                {
                    "type": "text",
                    "text": article_info.get('title', 'Untitled')[:100],
                    "size": "lg",
                    "weight": "bold",
                    "wrap": True,
                    "margin": "md",
                    "maxLines": 3
                }
            ],
            "paddingAll": "20px",
            "backgroundColor": "#f0f0f0"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": "👤",
                            "size": "sm",
                            "flex": 0
                        },
                        {
                            "type": "text",
                            "text": article_info.get('author', 'Unknown')[:50],
                            "size": "sm",
                            "color": "#555555",
                            "margin": "sm",
                            "flex": 1,
                            "wrap": True
                        }
                    ],
                    "margin": "sm"
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": "⏱️",
                            "size": "sm",
                            "flex": 0
                        },
                        {
                            "type": "text",
                            "text": article_info.get('reading_time', 'N/A'),
                            "size": "sm",
                            "color": "#555555",
                            "margin": "sm",
                            "flex": 1
                        }
                    ],
                    "margin": "sm"
                },
                {
                    "type": "separator",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": article_info.get('description', '')[:200],
                    "size": "sm",
                    "color": "#666666",
                    "wrap": True,
                    "margin": "md",
                    "maxLines": 4
                }
            ],
            "paddingAll": "20px"
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "uri",
                        "label": "📖 Read Article",
                        "uri": article_info.get('url', 'https://example.com')
                    },
                    "style": "primary",
                    "color": "#27ACB2",
                    "height": "sm"
                },
                {
                    "type": "button",
                    "action": {
                        "type": "message",
                        "label": "✅ Mark as Read",
                        "text": f"/read {row_number}"
                    },
                    "style": "secondary",
                    "height": "sm",
                    "margin": "sm"
                }
            ],
            "paddingAll": "20px",
            "backgroundColor": "#f9f9f9"
        }
    }

def get_category_color(category):
    colors = {
        'AI/Tech': '#4A90E2',
        'Programming': '#7B68EE',
        'Business': '#FF9500',
        'Design': '#FF6B6B',
        'Science': '#4ECDC4',
        'Health': '#95E1D3',
        'Education': '#F38181',
        'General': '#95A5A6'
    }
    return colors.get(category, '#95A5A6')

def create_error_message(error_details):
    return f"""❌ Error Processing Article

{error_details}

Please try again or send a different URL.
If the problem persists, the website might be blocking automated access."""

def create_welcome_message():
    return {
        "type": "bubble",
        "hero": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "📚",
                    "size": "3xl",
                    "align": "center"
                },
                {
                    "type": "text",
                    "text": "Article Saver Bot",
                    "size": "xl",
                    "weight": "bold",
                    "align": "center",
                    "margin": "md"
                }
            ],
            "backgroundColor": "#27ACB2",
            "paddingAll": "30px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "Welcome! I'll help you save and organize articles.",
                    "wrap": True,
                    "size": "md",
                    "margin": "md"
                },
                {
                    "type": "separator",
                    "margin": "lg"
                },
                {
                    "type": "text",
                    "text": "How to use:",
                    "weight": "bold",
                    "size": "md",
                    "margin": "lg"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "1. Send me any article URL",
                            "size": "sm",
                            "margin": "sm"
                        },
                        {
                            "type": "text",
                            "text": "2. I'll extract the information",
                            "size": "sm",
                            "margin": "sm"
                        },
                        {
                            "type": "text",
                            "text": "3. Save it to your Google Sheet",
                            "size": "sm",
                            "margin": "sm"
                        }
                    ],
                    "margin": "md"
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "message",
                        "label": "📖 View Commands",
                        "text": "/help"
                    },
                    "style": "primary",
                    "color": "#27ACB2"
                }
            ],
            "paddingAll": "20px"
        }
    }

def create_stats_flex(stats):
    return {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "📊 Your Reading Statistics",
                    "color": "#ffffff",
                    "size": "lg",
                    "weight": "bold"
                }
            ],
            "backgroundColor": "#27ACB2",
            "paddingAll": "20px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": str(stats['total']),
                                    "size": "xxl",
                                    "weight": "bold",
                                    "align": "center",
                                    "color": "#27ACB2"
                                },
                                {
                                    "type": "text",
                                    "text": "Total Articles",
                                    "size": "xs",
                                    "align": "center",
                                    "color": "#666666"
                                }
                            ],
                            "flex": 1
                        },
                        {
                            "type": "separator",
                            "margin": "sm"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": str(stats['read']),
                                    "size": "xxl",
                                    "weight": "bold",
                                    "align": "center",
                                    "color": "#4ECDC4"
                                },
                                {
                                    "type": "text",
                                    "text": "Read",
                                    "size": "xs",
                                    "align": "center",
                                    "color": "#666666"
                                }
                            ],
                            "flex": 1,
                            "margin": "sm"
                        },
                        {
                            "type": "separator",
                            "margin": "sm"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": str(stats['unread']),
                                    "size": "xxl",
                                    "weight": "bold",
                                    "align": "center",
                                    "color": "#FF9500"
                                },
                                {
                                    "type": "text",
                                    "text": "Unread",
                                    "size": "xs",
                                    "align": "center",
                                    "color": "#666666"
                                }
                            ],
                            "flex": 1,
                            "margin": "sm"
                        }
                    ],
                    "margin": "lg"
                },
                {
                    "type": "separator",
                    "margin": "xl"
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": "Top Category:",
                            "size": "sm",
                            "color": "#666666",
                            "flex": 0
                        },
                        {
                            "type": "text",
                            "text": stats['top_category'],
                            "size": "sm",
                            "weight": "bold",
                            "align": "end",
                            "flex": 1
                        }
                    ],
                    "margin": "lg"
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": "Total Reading Time:",
                            "size": "sm",
                            "color": "#666666",
                            "flex": 0
                        },
                        {
                            "type": "text",
                            "text": f"{stats['total_time']} min",
                            "size": "sm",
                            "weight": "bold",
                            "align": "end",
                            "flex": 1
                        }
                    ],
                    "margin": "md"
                }
            ],
            "paddingAll": "20px"
        }
    }