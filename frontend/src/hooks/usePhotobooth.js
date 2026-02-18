import { useState, useCallback, useRef, useEffect } from 'react'

export default function usePhotobooth() {
    const [status, setStatus] = useState('ready')
    const [statusIcon, setStatusIcon] = useState('📷')
    const [statusMessage, setStatusMessage] = useState('Ready to capture!')
    const [countdownValue, setCountdownValue] = useState(null)
    const [showCountdown, setShowCountdown] = useState(false)
    const [showFlash, setShowFlash] = useState(false)
    const [resultPhoto, setResultPhoto] = useState(null)
    const [isCapturing, setIsCapturing] = useState(false)

    const pollingRef = useRef(false)
    const flashedRef = useRef(false)

    const updateStatus = useCallback((newStatus, icon, message) => {
        setStatus(newStatus)
        setStatusIcon(icon)
        setStatusMessage(message)
    }, [])

    const triggerFlash = useCallback(() => {
        setShowFlash(true)
        setTimeout(() => setShowFlash(false), 200)
    }, [])

    const resetToReady = useCallback(() => {
        updateStatus('ready', '📷', 'Ready to capture!')
        setShowCountdown(false)
        setCountdownValue(null)
        setIsCapturing(false)
    }, [updateStatus])

    const poll = useCallback(async () => {
        if (!pollingRef.current) return

        try {
            const response = await fetch('/api/status')
            const data = await response.json()

            if (data.status === 'countdown') {
                const remaining = Math.ceil(data.target_timestamp - Date.now() / 1000)
                setShowCountdown(true)
                setCountdownValue(remaining > 0 ? remaining : '📸')
                updateStatus('capturing', '⏱️', data.message || `Get ready... ${remaining}`)
                flashedRef.current = false
            } else if (data.status === 'capturing') {
                setShowCountdown(true)
                setCountdownValue('📸')
                if (!flashedRef.current) {
                    triggerFlash()
                    flashedRef.current = true
                }
                updateStatus('capturing', '📸', data.message)
            } else if (data.status === 'waiting') {
                const remaining = Math.ceil(data.target_timestamp - Date.now() / 1000)
                setShowCountdown(true)
                setCountdownValue('✋')
                updateStatus('capturing', '✋', `${data.message} (${remaining}s)`)
                flashedRef.current = false
            } else if (data.status === 'processing') {
                setShowCountdown(true)
                setCountdownValue('🖨️')
                updateStatus('capturing', '🖨️', data.message)
            } else if (data.status === 'success') {
                pollingRef.current = false
                setShowCountdown(false)
                if (data.photo_url) {
                    setResultPhoto(data.photo_url)
                } else {
                    updateStatus('success', '🎉', data.message)
                    setTimeout(resetToReady, 3000)
                }
            } else if (data.status === 'error') {
                pollingRef.current = false
                setShowCountdown(false)
                updateStatus('error', '❌', data.message)
                setIsCapturing(false)
            }
        } catch (error) {
            // Keep polling on network errors
        }

        if (pollingRef.current) {
            setTimeout(poll, 200)
        }
    }, [updateStatus, triggerFlash, resetToReady])

    const startPolling = useCallback(() => {
        if (pollingRef.current) return
        pollingRef.current = true
        poll()
    }, [poll])

    const stopPolling = useCallback(() => {
        pollingRef.current = false
    }, [])

    const runCountdown = useCallback(async (seconds, text) => {
        return new Promise((resolve) => {
            let remaining = seconds
            setShowCountdown(true)
            setCountdownValue(remaining)
            updateStatus('capturing', '📷', `${text} - Get ready!`)

            const interval = setInterval(() => {
                remaining--
                if (remaining > 0) {
                    setCountdownValue(remaining)
                    updateStatus('capturing', '⏱️', `${text} in ${remaining}...`)
                } else {
                    clearInterval(interval)
                    setCountdownValue('📸')
                    triggerFlash()
                    updateStatus('capturing', '📸', 'SNAP!')
                    setTimeout(resolve, 200)
                }
            }, 1000)
        })
    }, [updateStatus, triggerFlash])

    const takePhoto = useCallback(async () => {
        if (isCapturing) return
        setIsCapturing(true)
        flashedRef.current = false

        const fetchPromise = fetch('/api/photo', { method: 'POST' })

        await runCountdown(3, '📸 Single Photo')
        updateStatus('capturing', '🖨️', 'Processing & printing...')

        try {
            const response = await fetchPromise
            const data = await response.json()

            if (response.ok) {
                startPolling()
            } else {
                setShowCountdown(false)
                updateStatus('error', '❌', data.message)
                setIsCapturing(false)
            }
        } catch (error) {
            setShowCountdown(false)
            updateStatus('error', '❌', 'Connection error')
            setIsCapturing(false)
        }
    }, [isCapturing, runCountdown, updateStatus, startPolling])

    const takeStrip = useCallback(async () => {
        if (isCapturing) return
        setIsCapturing(true)
        flashedRef.current = false

        try {
            const response = await fetch('/api/strip', { method: 'POST' })
            const data = await response.json()

            if (!response.ok) {
                updateStatus('error', '❌', data.message)
                setIsCapturing(false)
                return
            }

            startPolling()
        } catch (error) {
            updateStatus('error', '❌', 'Connection error')
            setIsCapturing(false)
        }
    }, [isCapturing, updateStatus, startPolling])

    const closeResult = useCallback(() => {
        setResultPhoto(null)
        resetToReady()
    }, [resetToReady])

    // Check initial status on mount
    useEffect(() => {
        fetch('/api/status')
            .then((r) => r.json())
            .then((data) => {
                if (data.in_progress) {
                    setIsCapturing(true)
                    startPolling()
                }
            })
            .catch(() => { })
    }, [startPolling])

    // Heartbeat: poll every 2s when idle to detect joystick-triggered captures
    useEffect(() => {
        if (isCapturing) return

        const interval = setInterval(async () => {
            try {
                const r = await fetch('/api/status')
                const data = await r.json()
                if (data.in_progress) {
                    setIsCapturing(true)
                    startPolling()
                }
            } catch {
                // ignore network errors
            }
        }, 2000)

        return () => clearInterval(interval)
    }, [isCapturing, startPolling])

    return {
        status,
        statusIcon,
        statusMessage,
        countdownValue,
        showCountdown,
        showFlash,
        resultPhoto,
        isCapturing,
        takePhoto,
        takeStrip,
        closeResult,
        stopPolling,
    }
}
