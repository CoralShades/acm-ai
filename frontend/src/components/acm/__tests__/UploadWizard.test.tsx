/**
 * Unit tests for UploadWizard step transitions (AC8)
 *
 * Story: E33-S1 Upload Wizard + Extraction Progress
 *
 * NOTE: This project does not currently have a test runner configured
 * (no Jest/Vitest in package.json). These tests are written using
 * Jest + React Testing Library syntax and are ready to run once a
 * test runner is added (e.g. `npm install --save-dev jest @testing-library/react
 * @testing-library/user-event @testing-library/jest-dom jest-environment-jsdom`).
 *
 * To activate: add "test": "jest" to package.json scripts and a jest.config.ts.
 */

import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { UploadWizard } from '../UploadWizard'
import { sourcesApi } from '@/lib/api/sources'
import { acmApi } from '@/lib/api/acm'

// ─── Mocks ────────────────────────────────────────────────────────────────────

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockRouterPush,
    refresh: jest.fn(),
  }),
}))

jest.mock('@/lib/api/sources', () => ({
  sourcesApi: {
    create: jest.fn(),
  },
}))

jest.mock('@/lib/api/acm', () => ({
  acmApi: {
    extract: jest.fn(),
  },
}))

jest.mock('@/lib/hooks/use-toast', () => ({
  useToast: () => ({
    error: jest.fn(),
    warning: jest.fn(),
    success: jest.fn(),
    toast: jest.fn(),
  }),
}))

const mockRouterPush = jest.fn()

// Helper: create a fake PDF File
function makePdfFile(name = 'test.pdf', size = 1024): File {
  const content = new Uint8Array(size).fill(37) // 0x25 = '%' (PDF magic byte lead)
  return new File([content], name, { type: 'application/pdf' })
}

// Helper: advance wizard to step 2 by selecting a file and clicking Next
async function advanceToStep2() {
  const fileInput = screen.getByTestId('file-input') as HTMLInputElement
  const pdfFile = makePdfFile()
  await userEvent.upload(fileInput, pdfFile)

  // Next button should now be enabled
  const nextBtn = screen.getByRole('button', { name: /next/i })
  await userEvent.click(nextBtn)
}

// Helper: advance to step 3
async function advanceToStep3() {
  await advanceToStep2()
  const nextBtn = screen.getByRole('button', { name: /next/i })
  await userEvent.click(nextBtn)
}

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('UploadWizard — step transitions', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Default sessionStorage mock
    Object.defineProperty(window, 'sessionStorage', {
      value: {
        getItem: jest.fn(),
        setItem: jest.fn(),
        removeItem: jest.fn(),
      },
      writable: true,
    })
  })

  test('Step 1 — Next button is disabled when no file is selected', () => {
    render(<UploadWizard />)
    const nextBtn = screen.getByRole('button', { name: /next/i })
    expect(nextBtn).toBeDisabled()
  })

  test('Step 1 — Next button is enabled after a PDF file is selected', async () => {
    render(<UploadWizard />)
    const fileInput = screen.getByTestId('file-input') as HTMLInputElement
    const pdfFile = makePdfFile()
    await userEvent.upload(fileInput, pdfFile)

    const nextBtn = screen.getByRole('button', { name: /next/i })
    expect(nextBtn).not.toBeDisabled()
  })

  test('Step 1 — Clicking Next advances to Step 2 content', async () => {
    render(<UploadWizard />)
    await advanceToStep2()

    expect(
      screen.getByText(/select extraction mode/i)
    ).toBeInTheDocument()
  })

  test('Step 2 — Mode defaults to standard', async () => {
    render(<UploadWizard />)
    await advanceToStep2()

    const standardCard = screen.getByTestId('mode-standard')
    expect(standardCard).toHaveAttribute('aria-pressed', 'true')
  })

  test('Step 2 — Selecting AI-Enhanced updates the selected mode', async () => {
    render(<UploadWizard />)
    await advanceToStep2()

    const aiCard = screen.getByTestId('mode-ai-enhanced')
    await userEvent.click(aiCard)

    expect(aiCard).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByTestId('mode-standard')).toHaveAttribute('aria-pressed', 'false')
  })

  test('Step 2 — Clicking Next advances to Step 3', async () => {
    render(<UploadWizard />)
    await advanceToStep3()

    // Step 3 content: confirm summary with Extract button
    expect(screen.getByTestId('extract-button')).toBeInTheDocument()
  })

  test('Step 3 — Shows the uploaded file name in the confirmation summary', async () => {
    render(<UploadWizard />)
    await advanceToStep3()

    expect(screen.getByTestId('confirm-file-name')).toHaveTextContent('test.pdf')
  })

  test('Cancel button on any step navigates to /jobs', async () => {
    render(<UploadWizard />)

    // Cancel on step 1
    const cancelBtn = screen.getByRole('button', { name: /cancel/i })
    await userEvent.click(cancelBtn)

    expect(mockRouterPush).toHaveBeenCalledWith('/jobs')
  })

  test('Step 3 — Clicking Extract triggers source creation then extraction and navigates', async () => {
    ;(sourcesApi.create as jest.Mock).mockResolvedValueOnce({ id: 'source:test123' })
    ;(acmApi.extract as jest.Mock).mockResolvedValueOnce({ command_id: 'cmd:abc' })

    render(<UploadWizard />)
    await advanceToStep3()

    const extractBtn = screen.getByTestId('extract-button')
    await userEvent.click(extractBtn)

    await waitFor(() => {
      expect(sourcesApi.create).toHaveBeenCalledTimes(1)
    })

    await waitFor(() => {
      expect(acmApi.extract).toHaveBeenCalledWith('source:test123')
    })

    await waitFor(() => {
      expect(mockRouterPush).toHaveBeenCalledWith(
        '/extraction/source%3Atest123'
      )
    })
  })

  test('Step 3 — Source creation failure shows fatal error dialog', async () => {
    ;(sourcesApi.create as jest.Mock).mockRejectedValueOnce(
      new Error('Network error')
    )

    render(<UploadWizard />)
    await advanceToStep3()

    const extractBtn = screen.getByTestId('extract-button')
    await userEvent.click(extractBtn)

    await waitFor(() => {
      expect(screen.getByText(/could not upload file/i)).toBeInTheDocument()
    })
  })
})
