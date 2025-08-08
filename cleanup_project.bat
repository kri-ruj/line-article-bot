@echo off
echo Starting cleanup of redundant files...

REM Delete redundant app versions
echo Deleting redundant app versions...
del app_firestore.py 2>nul
del app_firestore_fixed.py 2>nul
del app_firestore_final.py 2>nul
del app_liff_integrated.py 2>nul
del app_mobile_optimized.py 2>nul
del app_production_complete.py 2>nul
del app_production_fixed.py 2>nul
del app_production_enhanced.py 2>nul
del app_production_persistent.py 2>nul
del app_production_persistent_fixed.py 2>nul
del app_with_logging.py 2>nul

REM Delete all test files
echo Deleting test files...
del test_*.py 2>nul

REM Delete all fix files
echo Deleting fix scripts...
del fix_*.py 2>nul
del apply_targeted_fixes.py 2>nul
del comprehensive_fix.py 2>nul
del final_fix.py 2>nul
del final_test.py 2>nul

REM Delete utility and migration files
echo Deleting utility files...
del migrate_*.py 2>nul
del export_data_structure.py 2>nul
del data_structure_report.py 2>nul
del diagnose_data_issue.py 2>nul
del check_firestore.py 2>nul
del force_deploy.py 2>nul
del restore_backup.py 2>nul
del view_summary.py 2>nul

REM Delete notification files
echo Deleting notification scripts...
del notify_*.py 2>nul

REM Delete update scripts
echo Deleting update scripts...
del update_*.py 2>nul

REM Delete verification scripts
echo Deleting verification scripts...
del verify_*.py 2>nul

REM Delete menu creation scripts
echo Deleting menu scripts...
del create_menu_image.py 2>nul
del create_beautiful_menu.py 2>nul
del create_rich_menu_api.py 2>nul
del setup_rich_menu.py 2>nul
del generate_icons.py 2>nul

REM Delete old markdown docs (keeping README and CLAUDE.md)
echo Deleting redundant documentation...
del github_setup.md 2>nul
del data_structure.md 2>nul
del ALTERNATIVE_DEPLOYMENT.md 2>nul
del AUTHENTICATION_FLOW.md 2>nul
del DASHBOARD_IMPROVEMENTS.md 2>nul
del DEPLOYMENT_STATUS.md 2>nul
del DEPLOYMENT_GUIDE.md 2>nul
del DEPLOY_NOW.md 2>nul
del HOW_TO_USE_10X.md 2>nul
del FIXES_APPLIED.md 2>nul
del PERSISTENCE_ISSUE.md 2>nul
del PERSISTENT_STORAGE.md 2>nul
del PRODUCTION_DEPLOYMENT.md 2>nul
del find_your_articles.md 2>nul
del line_login_info.md 2>nul
del setup_guide.md 2>nul

echo.
echo Cleanup completed!
echo.
echo Files kept:
dir /b *.py
echo.
pause