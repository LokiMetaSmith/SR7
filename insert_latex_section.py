import re

filepath = "Fan made Shadowrun 7th Edition rules.tex"

with open(filepath, "r") as f:
    text = f.read()

# The content to insert
insertion = r"""\paragraph{3. Host Architecture \& Intrusion Countermeasures (IC)}\label{host-architecture-ic}

The Matrix is merged with the physical environment, meaning "Hosts" are no longer purely digital constructs floating in virtual space. A Host is a localized, biological biome of nanites and living crystal physically anchored in meatspace (a "Data-Hive").

\begin{itemize}[nosep]
    \item \textbf{Entering a Host:} You don't just "jack in" from across the world. A hacker must establish a tether to the physical perimeter of the Data-Hive or physically enter the nanite-saturated area. The Host's Rating (1-10) dictates its Firewall, Data Processing, and the physical density of the grey goo defending it.
    \item \textbf{Host Ratings \& Attributes:}
    \begin{itemize}[nosep]
        \item \textbf{Low (Rating 1-3):} Local mom-and-pop shops, gang hideouts. The nanites are sparse, mostly functioning as AR tags and basic security.
        \item \textbf{Medium (Rating 4-6):} Corporate offices, secure facilities. The air is thick with glowing dust; the environment actively responds to authorized users.
        \item \textbf{High (Rating 7-9):} Black sites, zero-zones. The walls themselves are composed of living crystal and data. The environment is actively hostile to intruders.
        \item \textbf{Apex (Rating 10):} God-tier constructs. The Host is indistinguishable from reality, bending physical laws within its perimeter.
    \end{itemize}
\end{itemize}

\textbf{Intrusion Countermeasures (IC)}
IC are not just digital avatars; they manifest physically as Dual-Natured entities formed from the ambient nanites. They can attack a hacker's persona via the tether or physically strike their meat-body.

\begin{itemize}[nosep]
    \item \textbf{Patrol IC ("Seeker Moths"):} Swarms of luminescent nanite-moths that flutter through the physical space of the Host, scanning for unauthorized tethers. If they spot a hacker, they alert the Host and attempt to attach themselves, placing a Tether on the intruder.
    \item \textbf{Killer IC ("Neon Hounds"):} Ferocious, canine-shaped constructs of jagged hard-light and crystal. They hunt down intruders and deal Stun Biofeedback damage.
    \item \textbf{Black IC ("Necrophages"):} Horrifying, insectoid monstrosities that latch onto a hacker's physical body or digital persona. They deal Physical damage and attempt to permanently sever the hacker's connection, causing severe Dumpshock and Essence drain.
    \item \textbf{Data IC ("The Librarians"):} Passive constructs that manage and encrypt the Host's data. If attacked, they deploy localized EMP bursts or attempt to scramble the hacker's cyberdeck.
\end{itemize}
"""

match = re.search(r'(\\paragraph\{2\. Matrix Actions \\& Tethers in\nCombat\}.*?)(\\hypertarget\{iii\.-rigging-vehicles-the-ghost-in-the-shell\})', text, re.DOTALL)

if match:
    new_text = text[:match.start(2)] + insertion + "\n" + text[match.start(2):]
    with open(filepath, "w") as f:
        f.write(new_text)
    print("Section inserted successfully.")
else:
    print("Could not find the insertion point.")
