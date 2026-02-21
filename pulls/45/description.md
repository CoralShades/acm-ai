## Description
This pull request integrates the following changes into the `main` branch from the `Sanju` branch:

1. **merge: integrate origin/main into Sanju with conflict resolution**
   - Resolved conflicts in the `package.json` file:
     - Removed the `lightningcss-linux-x64-gnu` dependency (to address compatibility issues in Windows).
     - Retained `lightningcss-win32-x64-msvc` to support Windows systems.
   - Regenerated `package-lock.json` after resolving the conflicts.
   - Includes fixes related to LF/CLRF issues, ensuring consistency across platform line endings (where identified).

2. **Fix bugs**
   - Applied fixes to address bugs within the codebase (precise details are available in the commit log).

## Type of Change
- [x] Bug fixes
- [x] Conflict resolution
- [x] Dependency adjustments

## Testing
The following testing has been applied to verify changes:
- [x] Local testing with Docker
- [x] Verification through manual testing

**Thank you for contributing to this effort!** 🎉