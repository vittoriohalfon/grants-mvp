'use client'

import { useState } from 'react'
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ArrowUpRight, Award, Briefcase, ChevronRight, DollarSign, FileText, Home, Settings, User } from "lucide-react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { ScrollArea } from "@/components/ui/scroll-area"

export function Dashboard() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)

  const grants = [
    {
      id: 1,
      name: "Green Energy Innovation Fund",
      description: "Supporting projects that develop innovative green energy solutions.",
      amount: 500000,
      eligibility: 95,
      status: "green"
    },
    {
      id: 2,
      name: "Small Business Growth Initiative",
      description: "Assisting small businesses in expanding their operations and creating jobs.",
      amount: 250000,
      eligibility: 80,
      status: "green"
    },
    {
      id: 3,
      name: "Tech Startup Accelerator Grant",
      description: "Boosting early-stage tech startups with funding and mentorship opportunities.",
      amount: 100000,
      eligibility: 65,
      status: "yellow"
    },
    {
      id: 4,
      name: "Rural Development Program",
      description: "Promoting economic growth and improving quality of life in rural areas.",
      amount: 150000,
      eligibility: 40,
      status: "red"
    },
  ]

  const contracts = [
    {
      id: 1,
      name: "Government IT Modernization Project",
      description: "Upgrading government IT infrastructure to improve efficiency and security.",
      amount: 2000000,
      eligibility: 85,
      status: "green"
    },
    {
      id: 2,
      name: "Public Infrastructure Maintenance",
      description: "Maintaining and improving public roads, bridges, and other infrastructure.",
      amount: 5000000,
      eligibility: 70,
      status: "yellow"
    },
    {
      id: 3,
      name: "Defense Technology Innovation",
      description: "Developing cutting-edge technologies for national defense applications.",
      amount: 1500000,
      eligibility: 60,
      status: "yellow"
    },
    {
      id: 4,
      name: "Healthcare Data Management System",
      description: "Creating a robust data management system for healthcare institutions.",
      amount: 3000000,
      eligibility: 30,
      status: "red"
    },
  ]

  const statusColors = {
    green: "bg-emerald-500",
    yellow: "bg-amber-500",
    red: "bg-rose-500",
  }

  const renderOpportunityCard = (item: { id: number; name: string; status: string; eligibility: number; description: string; amount: number }, type: string) => (
    <Card key={item.id} className="w-full transition-all hover:shadow-lg">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-lg font-semibold">
          {item.name}
        </CardTitle>
        <Badge variant="outline" className={`${statusColors[item.status as keyof typeof statusColors]} text-white font-medium px-2 py-1`}>
          {item.eligibility}% Match
        </Badge>
      </CardHeader>
      <CardContent>
        <CardDescription className="mt-2 mb-4 line-clamp-2">{item.description}</CardDescription>
        <div className="text-3xl font-bold text-primary">${item.amount.toLocaleString()}</div>
        <Progress value={item.eligibility} className="mt-4" />
        <div className="mt-6 flex justify-between">
          <Button size="sm" variant="outline">
            View Details
          </Button>
          <Button size="sm">
            Apply Now
            <ArrowUpRight className="ml-2 h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  )

  return (
    <div className="flex h-screen overflow-hidden bg-gray-100">
      {/* Sidebar */}
      <aside className={`bg-white w-64 h-screen flex-shrink-0 fixed left-0 top-0 z-20 transition-transform duration-300 ease-in-out ${isSidebarOpen ? 'translate-x-0' : '-translate-x-64'}`}>
        <div className="p-4 border-b">
          <div className="flex items-center space-x-4">
            <Avatar>
              <AvatarImage src="/placeholder-avatar.jpg" alt="User" />
              <AvatarFallback>JD</AvatarFallback>
            </Avatar>
            <div>
              <h2 className="font-semibold">John Doe</h2>
              <p className="text-sm text-gray-500">Acme Inc.</p>
            </div>
          </div>
        </div>
        <nav className="flex-1 p-4">
          <ul className="space-y-2">
            <li>
              <Button variant="ghost" className="w-full justify-start">
                <Home className="mr-2 h-4 w-4" />
                Dashboard
              </Button>
            </li>
            <li>
              <Button variant="ghost" className="w-full justify-start">
                <User className="mr-2 h-4 w-4" />
                Company Profile
              </Button>
            </li>
            <li>
              <Button variant="ghost" className="w-full justify-start">
                <Settings className="mr-2 h-4 w-4" />
                Settings
              </Button>
            </li>
          </ul>
        </nav>
      </aside>

      {/* Main Content */}
      <main className={`flex-1 overflow-x-hidden overflow-y-auto transition-all duration-300 ease-in-out ${isSidebarOpen ? 'ml-64' : 'ml-0'}`}>
        <div className="container mx-auto p-6 space-y-8 max-w-7xl">
          <header className="flex justify-between items-center">
            <div className="space-y-1">
              <h1 className="text-3xl font-bold tracking-tight">Funding Opportunities Dashboard</h1>
              <p className="text-xl text-muted-foreground">Discover grants and contracts tailored to your business</p>
            </div>
            <Button onClick={() => setIsSidebarOpen(!isSidebarOpen)} size="icon" variant="outline">
              <ChevronRight className={`h-4 w-4 transition-transform duration-200 ${isSidebarOpen ? 'rotate-180' : ''}`} />
              <span className="sr-only">Toggle Sidebar</span>
            </Button>
          </header>
          
          <ScrollArea className="h-[calc(100vh-8rem)]">
            <Tabs defaultValue="grants" className="space-y-6">
              <TabsList className="grid w-full grid-cols-2 max-w-md mx-auto">
                <TabsTrigger value="grants" className="text-lg">Grants</TabsTrigger>
                <TabsTrigger value="contracts" className="text-lg">Government Contracts</TabsTrigger>
              </TabsList>
              <TabsContent value="grants" className="space-y-6">
                <div className="grid gap-6 md:grid-cols-2">
                  {grants.map(grant => renderOpportunityCard(grant, 'grant'))}
                </div>
              </TabsContent>
              <TabsContent value="contracts" className="space-y-6">
                <div className="grid gap-6 md:grid-cols-2">
                  {contracts.map(contract => renderOpportunityCard(contract, 'contract'))}
                </div>
              </TabsContent>
            </Tabs>

            <div className="mt-12">
              <h2 className="text-2xl font-semibold mb-6">Analytics Overview</h2>
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
                <Card className="transition-all hover:shadow-md">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      Total Opportunities
                    </CardTitle>
                    <FileText className="h-5 w-5 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{grants.length + contracts.length}</div>
                    <p className="text-xs text-muted-foreground">Available funding options</p>
                  </CardContent>
                </Card>
                <Card className="transition-all hover:shadow-md">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      Potential Funding
                    </CardTitle>
                    <DollarSign className="h-5 w-5 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      ${(grants.reduce((sum, g) => sum + g.amount, 0) + contracts.reduce((sum, c) => sum + c.amount, 0)).toLocaleString()}
                    </div>
                    <p className="text-xs text-muted-foreground">Total available amount</p>
                  </CardContent>
                </Card>
                <Card className="transition-all hover:shadow-md">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Grants</CardTitle>
                    <Award className="h-5 w-5 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{grants.length}</div>
                    <p className="text-xs text-muted-foreground">Non-repayable funds</p>
                  </CardContent>
                </Card>
                <Card className="transition-all hover:shadow-md">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Contracts</CardTitle>
                    <Briefcase className="h-5 w-5 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{contracts.length}</div>
                    <p className="text-xs text-muted-foreground">Government opportunities</p>
                  </CardContent>
                </Card>
              </div>
            </div>
          </ScrollArea>
        </div>
      </main>
    </div>
  )
}