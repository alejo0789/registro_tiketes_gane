---
name: Acertemos Premium UI
description: Skill to replicate the polished user interface of the Acertemos form platform, including the brand header, interactive cards, and conversational chat-style forms.
---

# Acertemos Premium UI Skill

This skill provides the CSS design tokens, global styles, and HTML components to replicate the premium look and feel of the "Formularios de Comportamiento Humano" project.

## Core Design System
The UI is built around a corporate identity using **Acertemos Blue** and **Acertemos Gold**.

### Main Colors
- **Primary (Acertemos Blue):** `#002a5c`
- **Accent (Acertemos Gold):** `#ffcc00`
- **Background:** `#f8fafc`
- **Success:** `#22c55e`

## Key Visual Elements

### 1. Brand Header ("Barra Amarilla")
The header features a deep blue background with a prominent yellow bottom border that gives it a professional, authoritative look.
- **CSS Class:** `.brand-header`
- **Visuals:** Blue background, 5px solid yellow border, subtle shadow.

### 2. Interactive Selection Cards
Used for navigating different forms or modules.
- **Features:** 
    - Hover lift effect (`transform: translateY(-8px)`).
    - Left-accent border in gold.
    - Smooth transitions and shadows.

### 3. Conversational "Chat" Interface
A modern way to present questions, imitating a messaging app like WhatsApp.
- **Bot Bubbles:** White background, subtle shadow, left-aligned.
- **User Bubbles:** Blue gradient background, white text, right-aligned.
- **Animations:** Messages slide and fade in from the bottom.

## Implementation Guide

### Step 1: Base Styles
Link the `resources/styles.css` file which contains the standard CSS variables (Design Tokens) and reset styles.

### Step 2: Brand Header
```html
<header class="brand-header">
    <img src="/assets/acertemos logo.png" alt="Logo" class="brand-logo">
</header>
```

### Step 3: Landing Cards
```html
<div class="featured-card">
    <div class="featured-icon">📝</div>
    <div class="featured-content">
        <h2 class="featured-title">Título del Formulario</h2>
        <p class="featured-description">Descripción breve aquí.</p>
    </div>
    <div class="featured-action">Iniciar</div>
</div>
```

### Step 4: Chat Message Structure
```html
<!-- Bot Message -->
<div class="message bot">
    <div class="message-avatar">...</div>
    <div class="message-bubble"><div class="message-text">Hola, ¿cómo estás?</div></div>
</div>

<!-- User Message -->
<div class="message user">
    <div class="message-avatar">...</div>
    <div class="message-bubble"><div class="message-text">¡Muy bien!</div></div>
</div>
```

## Resources Included
- `resources/styles.css`: Full design system and layout logic.
- `resources/components/`: HTML templates for quick replication.
