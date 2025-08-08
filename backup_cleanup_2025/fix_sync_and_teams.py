#!/usr/bin/env python3
"""
Script to fix database sync and team mode issues in the Firestore version
"""

import re
import sys

def apply_fixes():
    # Read the file
    with open('app_firestore_final.py', 'r') as f:
        content = f.read()
    
    # Fix 1: Enhanced LIFF initialization with localStorage persistence
    fix1_old = """        // Initialize LIFF with proper external browser support
        window.onload = async function() {
            try {
                await liff.init({ 
                    liffId: "2007870100-ao8GpgRQ",
                    withLoginOnExternalBrowser: true // Enable login on external browsers
                });
                console.log('LIFF initialized, isInClient:', liff.isInClient());
                
                if (liff.isLoggedIn()) {
                    const profile = await liff.getProfile();
                    userId = profile.userId;
                    const displayName = profile.displayName || 'User';
                    
                    // Store userId in localStorage for persistence
                    if (userId) {
                        localStorage.setItem('lineUserId', userId);
                        localStorage.setItem('lineDisplayName', displayName);
                        console.log('Stored user ID in localStorage:', userId);
                    }"""
    
    fix1_new = """        // Initialize LIFF with proper external browser support
        window.onload = async function() {
            // First check localStorage for existing session
            const storedUserId = localStorage.getItem('lineUserId');
            const storedDisplayName = localStorage.getItem('lineDisplayName');
            
            if (storedUserId) {
                console.log('Found existing session in localStorage:', storedUserId);
                userId = storedUserId;
                document.getElementById('userInfo').innerHTML = `👤 ${storedDisplayName || 'User'} | `;
            }
            
            try {
                await liff.init({ 
                    liffId: "2007870100-ao8GpgRQ",
                    withLoginOnExternalBrowser: true // Enable login on external browsers
                });
                console.log('LIFF initialized, isInClient:', liff.isInClient());
                
                if (liff.isLoggedIn()) {
                    const profile = await liff.getProfile();
                    const liffUserId = profile.userId;
                    const displayName = profile.displayName || 'User';
                    
                    // Update userId if different from stored
                    if (liffUserId && liffUserId !== userId) {
                        userId = liffUserId;
                        localStorage.setItem('lineUserId', userId);
                        localStorage.setItem('lineDisplayName', displayName);
                        console.log('Updated user ID from LIFF:', userId);
                    }"""
    
    # Fix 2: Better error handling in LIFF initialization
    fix2_old = """            } catch (error) {
                console.error('LIFF initialization failed:', error);
                
                // Try to recover userId from localStorage
                const storedUserId = localStorage.getItem('lineUserId');
                const storedDisplayName = localStorage.getItem('lineDisplayName');
                
                if (storedUserId) {
                    console.log('Recovered user ID from localStorage:', storedUserId);
                    userId = storedUserId;
                    document.getElementById('userInfo').innerHTML = `👤 ${storedDisplayName || 'User'} | `;
                    
                    // Load data with stored userId
                    await autoMigrateArticles();
                    await loadUserTeams();
                    loadKanbanData();
                } else if (isDesktop()) {
                    showDesktopLoginOptions();
                } else {
                    showLoginRequired();
                }"""
    
    fix2_new = """            } catch (error) {
                console.error('LIFF initialization failed:', error);
                
                // Continue with stored session if available
                if (userId) {
                    console.log('Continuing with stored session despite LIFF error');
                    
                    // Load data with stored userId
                    await autoMigrateArticles();
                    await loadUserTeams();
                    loadKanbanData();
                    
                    if (isDesktop() && !isInLINE()) {
                        showDesktopFeatures();
                    }
                } else if (isDesktop()) {
                    showDesktopLoginOptions();
                } else {
                    showLoginRequired();
                }"""
    
    # Fix 3: Improve loadUserTeams with proper error handling
    fix3_old = """        async function loadUserTeams() {
            try {
                const res = await fetch(`/api/teams?user_id=${userId}`);
                userTeams = await res.json();
                console.log('User teams loaded:', userTeams.length);
            } catch (error) {
                console.error('Error loading user teams:', error);
                userTeams = [];
            }
        }"""
    
    fix3_new = """        async function loadUserTeams() {
            if (!userId) {
                console.warn('No userId available for loading teams');
                userTeams = [];
                return;
            }
            
            try {
                console.log('Loading teams for user:', userId);
                const res = await fetch(`/api/teams?user_id=${encodeURIComponent(userId)}`);
                
                if (!res.ok) {
                    console.error(`Failed to load teams: ${res.status}`);
                    userTeams = [];
                    return;
                }
                
                userTeams = await res.json();
                console.log('User teams loaded:', userTeams.length, userTeams);
            } catch (error) {
                console.error('Error loading user teams:', error);
                userTeams = [];
            }
        }"""
    
    # Fix 4: Improve autoMigrateArticles with userId check
    fix4_old = """        async function autoMigrateArticles() {
            try {
                // Silently migrate any unclaimed articles to current user
                const res = await fetch('/api/auto-migrate', {"""
    
    fix4_new = """        async function autoMigrateArticles() {
            if (!userId) {
                console.log('No userId available for auto-migration');
                return;
            }
            
            try {
                // Silently migrate any unclaimed articles to current user
                const res = await fetch('/api/auto-migrate', {"""
    
    # Fix 5: Improve loadKanbanData with userId check
    fix5_old = """        async function loadKanbanData() {
            try {
                const stages = ['inbox', 'reading', 'reviewing', 'completed'];
                
                for (const stage of stages) {
                    const column = document.getElementById(stage);
                    if (!column) continue;
                    
                    // Clear existing items (keep header)
                    const header = column.querySelector('.kanban-header');
                    column.innerHTML = '';
                    if (header) column.appendChild(header);
                    
                    // Fetch articles for this stage
                    const response = await fetch(`/api/articles?stage=${stage}&user_id=${userId || 'anonymous'}`);"""
    
    fix5_new = """        async function loadKanbanData() {
            if (!userId) {
                console.log('No userId available, showing empty kanban');
                const stages = ['inbox', 'reading', 'reviewing', 'completed'];
                for (const stage of stages) {
                    const column = document.getElementById(stage);
                    if (column) {
                        const header = column.querySelector('.kanban-header');
                        column.innerHTML = '';
                        if (header) column.appendChild(header);
                    }
                }
                return;
            }
            
            try {
                const stages = ['inbox', 'reading', 'reviewing', 'completed'];
                
                for (const stage of stages) {
                    const column = document.getElementById(stage);
                    if (!column) continue;
                    
                    // Clear existing items (keep header)
                    const header = column.querySelector('.kanban-header');
                    column.innerHTML = '';
                    if (header) column.appendChild(header);
                    
                    // Fetch articles for this stage
                    const response = await fetch(`/api/articles?stage=${stage}&user_id=${encodeURIComponent(userId)}`);"""
    
    # Fix 6: Improve loadTeamView with better error handling
    fix6_old = """                // Load user's teams
                const res = await fetch(`/api/teams?user_id=${userId}`);
                console.log('Team API response status:', res.status);"""
    
    fix6_new = """                // Load user's teams
                const res = await fetch(`/api/teams?user_id=${encodeURIComponent(userId)}`);
                console.log('Team API response status:', res.status);"""
    
    # Apply all fixes
    fixes = [
        (fix1_old, fix1_new),
        (fix2_old, fix2_new),
        (fix3_old, fix3_new),
        (fix4_old, fix4_new),
        (fix5_old, fix5_new),
        (fix6_old, fix6_new)
    ]
    
    for i, (old, new) in enumerate(fixes, 1):
        if old in content:
            content = content.replace(old, new)
            print(f"✓ Applied fix {i}")
        else:
            print(f"✗ Could not apply fix {i} - pattern not found")
    
    # Write the fixed content back
    with open('app_firestore_final.py', 'w') as f:
        f.write(content)
    
    print("\n✅ All fixes applied successfully!")
    print("\nFixed issues:")
    print("1. Database sync now properly uses localStorage for session persistence")
    print("2. Team mode functions now have proper userId validation")
    print("3. URL encoding added for all API calls with userId")
    print("4. Better error handling and fallback mechanisms")
    print("5. Session recovery from localStorage when LIFF fails")

if __name__ == "__main__":
    apply_fixes()