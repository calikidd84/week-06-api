from database import SessionLocal, engine
from models import Base, Book


GENRE_BOOKS = {
    "Sci-fi": [
        ("The Long Way to a Small, Angry Planet", "Becky Chambers", "Found-family space travel with warm character-driven science fiction."),
        ("Dune", "Frank Herbert", "Political ecology, prophecy, and survival on a desert planet."),
        ("Neuromancer", "William Gibson", "Cyberpunk hackers, artificial intelligence, and corporate power."),
        ("Project Hail Mary", "Andy Weir", "A lone scientist solves an interstellar extinction problem."),
        ("The Left Hand of Darkness", "Ursula K. Le Guin", "Anthropological science fiction about culture, identity, and diplomacy."),
        ("Kindred", "Octavia E. Butler", "Time travel that confronts American slavery and family history."),
        ("The Martian", "Andy Weir", "Engineering survival story set on Mars."),
        ("Children of Time", "Adrian Tchaikovsky", "Evolutionary space opera about humans and an emerging spider civilization."),
        ("All Systems Red", "Martha Wells", "A security android wants entertainment more than heroism."),
        ("Snow Crash", "Neal Stephenson", "Satirical cyberpunk adventure through virtual worlds and fractured America."),
    ],
    "Comic books": [
        ("Watchmen", "Alan Moore", "A layered superhero mystery about power, politics, and morality."),
        ("Batman: Year One", "Frank Miller", "A grounded origin story for Batman and Commissioner Gordon."),
        ("Ms. Marvel: No Normal", "G. Willow Wilson", "A teen superhero story about identity, family, and community."),
        ("Saga, Vol. 1", "Brian K. Vaughan", "Space fantasy about family, war, and survival."),
        ("Maus", "Art Spiegelman", "A graphic memoir about the Holocaust and inherited trauma."),
        ("The Sandman: Preludes and Nocturnes", "Neil Gaiman", "Mythic dark fantasy about dreams and stories."),
        ("V for Vendetta", "Alan Moore", "Dystopian resistance story about authoritarianism and freedom."),
        ("Spider-Man: Miles Morales", "Brian Michael Bendis", "A new Spider-Man balances heroics, school, and family."),
        ("Persepolis", "Marjane Satrapi", "Graphic memoir of growing up during the Iranian Revolution."),
        ("Kingdom Come", "Mark Waid", "Painted superhero epic about legacy and responsibility."),
    ],
    "Manga": [
        ("Fullmetal Alchemist, Vol. 1", "Hiromu Arakawa", "Alchemy, brotherhood, and consequences in a military fantasy world."),
        ("Death Note, Vol. 1", "Tsugumi Ohba", "A tense battle of wits around a notebook with lethal power."),
        ("One Piece, Vol. 1", "Eiichiro Oda", "Pirate adventure built around friendship, freedom, and treasure."),
        ("Naruto, Vol. 1", "Masashi Kishimoto", "A young ninja seeks recognition and mastery."),
        ("Attack on Titan, Vol. 1", "Hajime Isayama", "Dark action fantasy about humanity behind walls."),
        ("Sailor Moon, Vol. 1", "Naoko Takeuchi", "Magical girl adventure with friendship and destiny."),
        ("My Hero Academia, Vol. 1", "Kohei Horikoshi", "A superhero academy story about courage and growth."),
        ("Vagabond, Vol. 1", "Takehiko Inoue", "Historical samurai drama inspired by Miyamoto Musashi."),
        ("Yotsuba&!, Vol. 1", "Kiyohiko Azuma", "Gentle slice-of-life comedy through a child's curious eyes."),
        ("Demon Slayer, Vol. 1", "Koyoharu Gotouge", "A brother fights demons to save his sister."),
    ],
    "Fantasy": [
        ("The Hobbit", "J.R.R. Tolkien", "Classic quest fantasy with dragons, riddles, and unexpected courage."),
        ("The Name of the Wind", "Patrick Rothfuss", "A gifted musician and magician recounts his legendary life."),
        ("A Wizard of Earthsea", "Ursula K. Le Guin", "Coming-of-age fantasy about pride, power, and balance."),
        ("Mistborn", "Brandon Sanderson", "Heist-driven epic fantasy with metal-based magic."),
        ("The Fifth Season", "N.K. Jemisin", "Apocalyptic fantasy about oppression, survival, and seismic magic."),
        ("The Priory of the Orange Tree", "Samantha Shannon", "Dragon-filled epic fantasy with queens, faith, and political alliances."),
        ("The Way of Kings", "Brandon Sanderson", "Large-scale fantasy about war, honor, and ancient powers."),
        ("Jonathan Strange & Mr Norrell", "Susanna Clarke", "Regency-era historical fantasy about English magic."),
        ("The Poppy War", "R.F. Kuang", "Military fantasy inspired by twentieth-century Chinese history."),
        ("Howl's Moving Castle", "Diana Wynne Jones", "Whimsical fantasy about curses, confidence, and a moving home."),
    ],
    "Fiction": [
        ("The Great Gatsby", "F. Scott Fitzgerald", "A lyrical portrait of wealth, longing, and reinvention."),
        ("To Kill a Mockingbird", "Harper Lee", "Southern courtroom fiction about justice and moral courage."),
        ("The Vanishing Half", "Brit Bennett", "Twin sisters choose different lives across race, family, and identity."),
        ("Tomorrow, and Tomorrow, and Tomorrow", "Gabrielle Zevin", "Friendship, ambition, and creativity in game development."),
        ("Little Fires Everywhere", "Celeste Ng", "Suburban family drama about motherhood, secrets, and privilege."),
        ("The Road", "Cormac McCarthy", "Spare post-apocalyptic journey of a father and son."),
        ("Normal People", "Sally Rooney", "Intimate literary fiction about class, love, and miscommunication."),
        ("Beloved", "Toni Morrison", "Haunting fiction about memory, slavery, and motherhood."),
        ("The Kite Runner", "Khaled Hosseini", "Friendship, betrayal, and redemption across Afghanistan and America."),
        ("A Gentleman in Moscow", "Amor Towles", "A count builds a meaningful life while confined inside a hotel."),
    ],
    "Non-fiction": [
        ("Sapiens", "Yuval Noah Harari", "A sweeping history of humankind and social imagination."),
        ("Educated", "Tara Westover", "Memoir about family, isolation, and self-directed learning."),
        ("The Immortal Life of Henrietta Lacks", "Rebecca Skloot", "Science history, medical ethics, and one family's story."),
        ("Thinking, Fast and Slow", "Daniel Kahneman", "Behavioral science about judgment, bias, and decision-making."),
        ("The Warmth of Other Suns", "Isabel Wilkerson", "Narrative history of the Great Migration."),
        ("Born a Crime", "Trevor Noah", "Memoir of growing up under apartheid and after."),
        ("Into Thin Air", "Jon Krakauer", "Personal account of disaster on Mount Everest."),
        ("The Omnivore's Dilemma", "Michael Pollan", "Investigation of food systems and modern eating."),
        ("Quiet", "Susan Cain", "Cultural and psychological look at introversion."),
        ("Bad Blood", "John Carreyrou", "Investigative account of Theranos and Silicon Valley deception."),
    ],
    "Sports": [
        ("Moneyball", "Michael Lewis", "Baseball analytics and the reinvention of team building."),
        ("The Boys in the Boat", "Daniel James Brown", "Olympic rowing story of teamwork and grit."),
        ("Friday Night Lights", "H.G. Bissinger", "High school football and community pressure in Texas."),
        ("Open", "Andre Agassi", "Tennis memoir about talent, pressure, and identity."),
        ("Shoe Dog", "Phil Knight", "Nike's origin story told by its founder."),
        ("Seabiscuit", "Laura Hillenbrand", "Racehorse biography set during the Great Depression."),
        ("The Mamba Mentality", "Kobe Bryant", "Basketball mindset, preparation, and competitive craft."),
        ("Relentless", "Tim S. Grover", "Training philosophy from an elite sports performance coach."),
        ("The Champion's Mind", "Jim Afremow", "Mental skills guide for athletic performance."),
        ("The Blind Side", "Michael Lewis", "Football, family, and the evolution of offensive strategy."),
    ],
    "Software": [
        ("Clean Code", "Robert C. Martin", "Practical guidance for writing readable, maintainable code."),
        ("The Pragmatic Programmer", "Andrew Hunt", "Timeless software craftsmanship habits and principles."),
        ("Design Patterns", "Erich Gamma", "Classic object-oriented patterns for reusable software design."),
        ("Refactoring", "Martin Fowler", "Techniques for improving code structure safely."),
        ("You Don't Know JS Yet", "Kyle Simpson", "Deep JavaScript language concepts for web developers."),
        ("Fluent Python", "Luciano Ramalho", "Idiomatic Python features, patterns, and internals."),
        ("Effective TypeScript", "Dan Vanderkam", "Practical advice for stronger TypeScript programs."),
        ("Database Design for Mere Mortals", "Michael J. Hernandez", "Relational database modeling for practical applications."),
        ("Site Reliability Engineering", "Betsy Beyer", "Google's practices for scalable, reliable production systems."),
        ("Accelerate", "Nicole Forsgren", "Research-backed software delivery and DevOps performance."),
    ],
    "Business": [
        ("The Lean Startup", "Eric Ries", "Startup experimentation, feedback loops, and validated learning."),
        ("Good to Great", "Jim Collins", "Research on companies that achieved sustained performance."),
        ("Atomic Habits", "James Clear", "Systems for building habits and improving behavior."),
        ("Zero to One", "Peter Thiel", "Contrarian startup thinking about monopolies and innovation."),
        ("The Innovator's Dilemma", "Clayton M. Christensen", "Why successful companies struggle with disruptive innovation."),
        ("Measure What Matters", "John Doerr", "Goal-setting with objectives and key results."),
        ("The Hard Thing About Hard Things", "Ben Horowitz", "Leadership lessons from difficult startup moments."),
        ("Start with Why", "Simon Sinek", "Purpose-driven leadership and communication."),
        ("Blue Ocean Strategy", "W. Chan Kim", "Creating new market space instead of competing directly."),
        ("Never Split the Difference", "Chris Voss", "Negotiation principles from an FBI hostage negotiator."),
    ],
    "How-to guides": [
        ("How to Win Friends and Influence People", "Dale Carnegie", "Practical communication and relationship-building advice."),
        ("Getting Things Done", "David Allen", "Personal productivity system for capturing and organizing work."),
        ("The Life-Changing Magic of Tidying Up", "Marie Kondo", "Home organization method focused on intentional ownership."),
        ("On Writing", "Stephen King", "Memoir and practical craft guide for writers."),
        ("The Artist's Way", "Julia Cameron", "Creative recovery program built around daily and weekly practices."),
        ("Salt, Fat, Acid, Heat", "Samin Nosrat", "Cooking fundamentals explained through four core elements."),
        ("The Total Money Makeover", "Dave Ramsey", "Step-by-step personal finance and debt reduction plan."),
        ("Deep Work", "Cal Newport", "How to protect focus for cognitively demanding work."),
        ("Make It Stick", "Peter C. Brown", "Evidence-based study methods for durable learning."),
        ("The First 20 Hours", "Josh Kaufman", "A framework for quickly learning new skills."),
    ],
        "History": [
        ("Guns, Germs, and Steel", "Jared Diamond", "A broad thesis on how geography and environment shaped global power."),
        ("A People's History of the United States", "Howard Zinn", "US history told from the perspectives of marginalized groups."),
        ("The Silk Roads", "Peter Frankopan", "A global history centered on trade routes between East and West."),
        ("The Rise and Fall of the Third Reich", "William L. Shirer", "A detailed narrative of Nazi Germany’s origins and collapse."),
        ("The Wright Brothers", "David McCullough", "Story of the brothers who pioneered powered flight."),
        ("Postwar", "Tony Judt", "A sweeping history of Europe from 1945 to the early 21st century."),
        ("The Liberation Trilogy", "Rick Atkinson", "Narrative history of the US Army’s role in liberating Europe in WWII."),
        ("The Guns of August", "Barbara W. Tuchman", "Account of the opening months of World War I."),
        ("SPQR: A History of Ancient Rome", "Mary Beard", "A fresh look at the politics and people of ancient Rome."),
        ("The Righteous Mind of the Civil War Era", "Fictional Example", "Explores moral and cultural conflicts leading up to the US Civil War."),
    ],
    "Biography": [
        ("Steve Jobs", "Walter Isaacson", "Biography of Apple’s cofounder covering his vision, flaws, and product obsessions."),
        ("Alexander Hamilton", "Ron Chernow", "Life of the US founding father behind modern finance and the hit musical."),
        ("Leonardo da Vinci", "Walter Isaacson", "Portrait of a Renaissance polymath connecting art, science, and curiosity."),
        ("Einstein: His Life and Universe", "Walter Isaacson", "Biography of the physicist whose ideas reshaped modern physics."),
        ("Catherine the Great: Portrait of a Woman", "Robert K. Massie", "Rise of a minor German princess to Empress of Russia."),
        ("Churchill: A Life", "Martin Gilbert", "Comprehensive account of Winston Churchill’s long political career."),
        ("The Snowball: Warren Buffett and the Business of Life", "Alice Schroeder", "Life of the famed investor, his habits, and philosophy."),
        ("The Autobiography of Malcolm X", "Malcolm X and Alex Haley", "First-person account of transformation, faith, and activism."),
        ("Long Walk to Freedom", "Nelson Mandela", "Memoir of struggle, imprisonment, and South Africa’s transition."),
        ("Einstein’s Wife: A Fictional Chronicle", "Fictional Example", "Imagined inner life of the woman beside a scientific icon."),
    ],
}


def seed_books():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        created = 0
        statuses = ["want_to_read", "reading", "read"]
        for genre, books in GENRE_BOOKS.items():
            for index, (title, author, description) in enumerate(books):
                exists = (
                    db.query(Book)
                    .filter(Book.title == title, Book.author == author)
                    .first()
                )
                if exists:
                    continue

                status = statuses[index % len(statuses)]
                rating = (index % 5) + 1 if status == "read" else None
                db.add(
                    Book(
                        title=title,
                        author=author,
                        genre=genre,
                        status=status,
                        rating=rating,
                        description=description,
                    )
                )
                created += 1

        db.commit()
        return created
    finally:
        db.close()


if __name__ == "__main__":
    created_count = seed_books()
    print(f"Seeded {created_count} new books.")
