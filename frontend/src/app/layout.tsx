import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Web DNA",
  description: "See how companies evolve on the web.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} min-h-screen bg-background text-foreground antialiased flex flex-col`}>
        <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="container flex h-14 max-w-screen-2xl items-center px-4">
                <div className="flex font-bold text-lg items-center space-x-2">
                    <span className="text-primary">WEB</span>
                    <span>DNA</span>
                </div>
            </div>
        </header>
        <main className="flex-1 container max-w-screen-2xl mx-auto p-4 sm:p-8">
            {children}
        </main>
      </body>
    </html>
  );
}
