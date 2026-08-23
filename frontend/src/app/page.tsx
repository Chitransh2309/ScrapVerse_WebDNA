"use client"

import { useCallback, useEffect, useState } from "react"
import { fetchCompanies, fetchGenome, fetchMutations, fetchAgentRuns, fetchScrapers, triggerSequence, fetchSequenceStatus, createCompany, API_BASE } from "@/lib/api"
import { Activity, AlertTriangle, ShieldAlert, Cpu, HeartPulse, RefreshCw, Plus } from "lucide-react"
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { format } from 'date-fns'

export default function Home() {
  const [companies, setCompanies] = useState<any[]>([])
  const [selectedCompanyId, setSelectedCompanyId] = useState<string | null>(null)

  const [genome, setGenome] = useState<any>(null)
  const [mutations, setMutations] = useState<any[]>([])
  const [agentRuns, setAgentRuns] = useState<any[]>([])
  const [scrapers, setScrapers] = useState<any[]>([])

  const [loading, setLoading] = useState(true)
  const [sequencing, setSequencing] = useState(false)
  const [sequenceStatus, setSequenceStatus] = useState<string | null>(null)
  const [sequenceError, setSequenceError] = useState<string | null>(null)
  const [newCompanyName, setNewCompanyName] = useState("")
  const [isAdding, setIsAdding] = useState(false)
  const [addError, setAddError] = useState<string | null>(null)

  // Polling state
  useEffect(() => {
    fetchCompanies().then(data => {
      setCompanies(data)
      if (data.length > 0) {
        setSelectedCompanyId(data[0].id)
      }
      setLoading(false)
    }).catch(e => {
      console.warn("Backend not ready:", e)
      setLoading(false)
    })
  }, [])

  const loadData = useCallback(() => {
    if (!selectedCompanyId) return
    fetchGenome(selectedCompanyId).then(data => {
      if (data && data.traits) setGenome(data)
      else setGenome(null)
    }).catch(() => {})
    fetchMutations(selectedCompanyId).then(data => setMutations(data)).catch(() => {})
    fetchAgentRuns(selectedCompanyId).then(data => setAgentRuns(data)).catch(() => {})
    fetchScrapers(selectedCompanyId).then(data => setScrapers(data)).catch(() => {})
    // Also refresh the companies list so a domain resolved in the background
    // (after adding a company) shows up without a manual refresh.
    fetchCompanies().then(data => setCompanies(data)).catch(() => {})
  }, [selectedCompanyId])

  useEffect(() => {
    if (!selectedCompanyId) return
    loadData()
    const interval = setInterval(loadData, 5000) // Poll every 5s for the dashboard
    return () => clearInterval(interval)
  }, [selectedCompanyId, loadData])

  const handleSequence = async () => {
    if (!selectedCompanyId) return
    setSequencing(true)
    setSequenceError(null)
    setSequenceStatus("queued")
    try {
      const job = await triggerSequence(selectedCompanyId)
      if (!job.job_id) throw new Error("No job id returned")

      // Poll the actual job status instead of assuming it's done after a fixed delay -
      // sequencing (genome build + mutation detection + agent investigations) can take
      // anywhere from seconds to several minutes.
      while (true) {
        await new Promise(r => setTimeout(r, 3000))
        const job_status = await fetchSequenceStatus(selectedCompanyId, job.job_id)
        setSequenceStatus(job_status.status)
        if (job_status.status === "completed" || job_status.status === "failed" || job_status.error) {
          break
        }
      }
    } catch (e) {
      console.error(e)
      setSequenceError("Failed to run sequence. Please try again.")
    } finally {
      setSequencing(false)
      loadData()
    }
  }

  const handleAddCompany = async () => {
    if (!newCompanyName.trim()) return
    setIsAdding(true)
    setAddError(null)
    try {
      const newCompany = await createCompany(newCompanyName.trim())
      const freshCompanies = await fetchCompanies()
      setCompanies(freshCompanies)
      setSelectedCompanyId(newCompany.id)
      setNewCompanyName("")
    } catch (e) {
      console.error(e)
      setAddError("Failed to add company. Please try again.")
    } finally {
      setIsAdding(false)
    }
  }

  if (loading) return <div className="p-8 text-center animate-pulse">Loading Web DNA...</div>
  if (!companies.length && !isAdding) return <div className="p-8 text-center text-muted-foreground">No companies found. Run the seed script.</div>

  const selectedCompany = companies.find(c => c.id === selectedCompanyId)

  // Chart data formatting
  const chartData = genome?.traits ? Object.entries(genome.traits).map(([name, score]) => ({
    name,
    score: Math.round((score as number) * 100)
  })) : []

  return (
    <div className="flex flex-col gap-8">
      {/* Header section */}
      <div className="flex justify-between items-end border-b border-border pb-4">
        <div>
          <div className="flex items-center gap-4 mb-2">
            <h1 className="text-4xl font-extrabold tracking-tight lg:text-5xl">{selectedCompany?.name || "No Company"}</h1>
            <select 
              value={selectedCompanyId || ''} 
              onChange={(e) => setSelectedCompanyId(e.target.value)}
              className="bg-secondary text-secondary-foreground text-sm rounded px-2 py-1 outline-none cursor-pointer"
            >
              {companies.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
            <div className="flex items-center gap-2 ml-4">
              <input 
                type="text" 
                placeholder="Company Name" 
                value={newCompanyName}
                onChange={e => setNewCompanyName(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleAddCompany()}
                className="bg-background border border-border text-sm rounded px-3 py-1 outline-none focus:ring-1 focus:ring-primary w-40"
              />
              <button
                onClick={handleAddCompany}
                disabled={isAdding || !newCompanyName.trim()}
                className="bg-secondary text-secondary-foreground hover:bg-secondary/80 px-3 py-1 rounded text-sm font-medium transition-colors disabled:opacity-50 flex items-center gap-1"
              >
                {isAdding ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Plus className="w-3 h-3" />}
                Add
              </button>
              {addError && <span className="text-xs text-red-400">{addError}</span>}
            </div>
          </div>
          <p className="text-muted-foreground text-lg">{selectedCompany?.domain || "---"}</p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <button
            onClick={handleSequence}
            disabled={sequencing || !selectedCompanyId}
            className="bg-primary text-primary-foreground px-6 py-2 rounded-md font-medium flex items-center gap-2 hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            {sequencing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Activity className="w-4 h-4" />}
            {sequencing ? `Sequencing... (${sequenceStatus})` : "Force Sequence"}
          </button>
          {sequenceError && <span className="text-xs text-red-400">{sequenceError}</span>}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Genome & Scrapers */}
        <div className="col-span-1 lg:col-span-2 flex flex-col gap-8">
          
          {/* Genome Chart */}
          <div className="bg-card text-card-foreground border rounded-lg p-6 shadow-sm">
            <h2 className="text-2xl font-semibold mb-6 flex items-center gap-2">
              <Cpu className="w-6 h-6 text-primary" /> Current Genome
            </h2>
            {chartData.length > 0 ? (
              <div className="h-[400px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#333" />
                    <XAxis type="number" domain={[0, 100]} stroke="#888" />
                    <YAxis dataKey="name" type="category" width={120} stroke="#888" tick={{ fill: '#ccc', fontSize: 12 }} />
                    <Tooltip contentStyle={{ backgroundColor: '#111', borderColor: '#333' }} />
                    <Bar dataKey="score" fill="hsl(262.1 83.3% 57.8%)" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-[400px] flex items-center justify-center text-muted-foreground">
                No genome sequence found. Run a sequence.
              </div>
            )}
          </div>

          {/* Scrapers Health */}
          <div className="bg-card text-card-foreground border rounded-lg p-6 shadow-sm">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <HeartPulse className="w-5 h-5 text-destructive" /> Data Sources Health
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {scrapers.map(s => (
                <div key={s.id} className="border p-4 rounded-md flex flex-col gap-2 bg-secondary/30">
                  <div className="flex justify-between items-start">
                    <span className="font-medium text-sm">{s.name}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${s.status === 'healthy' || s.status === 'healed' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                      {s.status}
                    </span>
                  </div>
                  <span className="text-xs text-muted-foreground font-mono truncate">{s.collector_id}</span>
                  {s.status === 'failing' && (
                    <div className="mt-2 flex gap-2">
                      <button 
                        className="bg-primary/20 text-primary text-xs px-3 py-1 rounded hover:bg-primary/30 cursor-pointer"
                        onClick={async () => {
                          if (!selectedCompanyId) return;
                          await fetch(`${API_BASE}/scrapers/${s.collector_id}/heal/approve`, { method: "POST" })
                          fetchScrapers(selectedCompanyId).then(data => setScrapers(data))
                        }}
                      >
                        Approve Healing
                      </button>
                    </div>
                  )}
                  {s.status === 'healthy' && (
                    <button 
                      className="text-xs text-muted-foreground hover:text-foreground mt-2 text-left cursor-pointer"
                      onClick={async () => {
                        if (!selectedCompanyId) return;
                        await fetch(`${API_BASE}/scrapers/${s.collector_id}/simulate_failure`, { method: "POST" })
                        fetchScrapers(selectedCompanyId).then(data => setScrapers(data))
                      }}
                    >
                      Simulate Failure
                    </button>
                  )}
                </div>
              ))}
              {scrapers.length === 0 && <span className="text-muted-foreground text-sm">No scrapers configured.</span>}
            </div>
          </div>
        </div>

        {/* Right Column: Agent & Mutations */}
        <div className="flex flex-col gap-8">
          
          {/* Recent Mutations */}
          <div className="bg-card text-card-foreground border rounded-lg p-6 shadow-sm">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-500" /> Recent Mutations
            </h2>
            <div className="flex flex-col gap-4 max-h-[300px] overflow-y-auto pr-2">
              {mutations.slice(0, 5).map(m => (
                <div key={m.id} className="flex flex-col gap-1 border-l-2 border-amber-500 pl-3 py-1">
                  <div className="flex justify-between items-center">
                    <span className="font-medium text-sm">{m.trait}</span>
                    <span className="text-xs font-mono px-2 py-0.5 rounded bg-muted">
                      {m.delta > 0 ? '+' : ''}{m.delta.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-xs text-muted-foreground">
                    <span>{m.mutation_type}</span>
                    <span className={m.severity === 'critical' ? 'text-red-400' : 'text-amber-400'}>{m.severity.toUpperCase()}</span>
                  </div>
                </div>
              ))}
              {mutations.length === 0 && <span className="text-muted-foreground text-sm">No recent mutations.</span>}
            </div>
          </div>

          {/* Agent Activity Feed */}
          <div className="bg-card text-card-foreground border rounded-lg p-6 shadow-sm flex-1">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-blue-500" /> Agent Activity
            </h2>
            <div className="flex flex-col gap-4 max-h-[400px] overflow-y-auto pr-2">
              {agentRuns.slice(0, 3).map(r => (
                <div key={r.id} className="border p-4 rounded-md bg-secondary/20 flex flex-col gap-3">
                  <div className="flex justify-between items-center border-b border-border/50 pb-2">
                    <span className="text-xs text-muted-foreground font-mono">{r.id.split('-')[0]}</span>
                    <span className={`text-xs px-2 py-0.5 rounded ${r.status === 'running' ? 'bg-blue-500/20 text-blue-400 animate-pulse' : 'bg-green-500/20 text-green-400'}`}>
                      {r.status}
                    </span>
                  </div>
                  {r.final_result ? (
                    <div className="text-sm">
                      <p className="font-semibold mb-1 text-primary">{r.final_result.summary}</p>
                      <p className="text-muted-foreground text-xs mt-2 line-clamp-3">{r.final_result.why_it_matters}</p>
                    </div>
                  ) : (
                    <div className="text-sm text-muted-foreground flex items-center gap-2">
                      <Activity className="w-4 h-4 animate-spin text-blue-400" /> Investigating {r.step_count} steps...
                    </div>
                  )}
                </div>
              ))}
              {agentRuns.length === 0 && <span className="text-muted-foreground text-sm">No agent investigations active.</span>}
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}
