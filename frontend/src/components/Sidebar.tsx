"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"

const items = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/environments", label: "Environments" },
  { href: "/cameras", label: "Cameras" },
  { href: "/users", label: "Users & Admins" },
  { href: "/settings", label: "Settings" },
]

export default function Sidebar() {
  const path = usePathname()

  return (
    <aside className="w-64 border-r bg-white h-screen sticky top-0">
      <div className="p-4">
        <div className="text-xl font-semibold">Third Eye</div>
        <div className="text-sm text-gray-500">Admin Console</div>
      </div>

      <nav className="p-2 space-y-1">
        {items.map((it) => {
          const active = path.startsWith(it.href)
          return (
            <Link
              key={it.href}
              href={it.href}
              className={[
                "block rounded-md px-3 py-2 text-sm",
                active ? "bg-gray-100 font-medium" : "hover:bg-gray-50",
              ].join(" ")}
            >
              {it.label}
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}
