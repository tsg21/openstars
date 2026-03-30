# Stars! Manual Chapter Cleanup

Status: ⏸️ Paused

## Goal

Clean up the split Stars! manual chapter files in `docs/references/manual/chapters/` so each chapter reads like intentional Markdown rather than raw PDF/OCR output.

## Scope

- Reformat one chapter at a time
- Preserve original meaning and technical content
- Normalize headings, paragraphs, numbered steps, and lists
- Remove obvious OCR/sidebar debris when it interrupts readability
- Leave source PDF and raw extraction untouched

## Chapters

- [x] Review and reformat `00-front-matter.md`
- [x] Review and reformat `01-welcome-to-the-stars-universe.md`
- [x] Review and reformat `02-single-player-setup.md`
- [x] Review and reformat `03-multi-player-setup.md`
- [x] Review and reformat `04-things-every-stars-player-should-know.md`
- [x] Review and reformat `05-the-stars-screen.md`
- [x] Review and reformat `06-planets.md`
- [x] Review and reformat `07-production.md`
- [x] Review and reformat `08-research.md`
- [x] Review and reformat `09-ship-and-starbase-design.md`
- [x] Review and reformat `10-managing-fleets.md`
- [x] Review and reformat `11-navigation.md`
- [x] Review and reformat `12-colonization.md`
- [x] Review and reformat `13-mining.md`
- [x] Review and reformat `14-transporting-freight.md`
- [x] Review and reformat `15-the-basics-of-combat.md`
- [x] Review and reformat `16-patrolling.md`
- [x] Review and reformat `17-scanning-and-cloaking.md`
- [x] Review and reformat `18-reports.md`
- [x] Review and reformat `19-diplomacy-and-trade.md`
- [x] Review and reformat `20-designing-custom-races.md`
- [x] Review and reformat `21-predefined-races.md`
- [x] Review and reformat `22-alternate-reality-races.md`
- [x] Review and reformat `23-the-guts-of-combat.md`
- [x] Review and reformat `24-the-guts-of-cloaking.md`
- [x] Review and reformat `25-the-guts-of-mass-drivers.md`
- [x] Review and reformat `26-the-guts-of-minefields.md`
- [x] Review and reformat `appendix-a-keyboard-shortcuts.md`
- [x] Review and reformat `appendix-b-technology-tables.md`
- [x] Review and reformat `appendix-c-files-used-in-stars.md`
- [x] Review and reformat `appendix-d-frequently-asked-questions.md`

## Finalization

- [ ] Review `docs/references/manual/README.md` links and descriptions after chapter cleanup
- [ ] Spot-check chapter-to-chapter consistency in heading levels and formatting

## Notes

- Proceed chapter by chapter in future sessions; do not batch-edit blindly.
- ✅ Completed `00-front-matter.md` by restructuring the title page, credits, contents, and introduction into readable Markdown and correcting obvious OCR issues.
- ✅ Completed `01-welcome-to-the-stars-universe.md` by normalizing split headings, cleaning prose formatting, and fixing obvious OCR and punctuation issues while preserving the original tone.
- ✅ Completed `02-single-player-setup.md` by converting the raw tutorial and setup instructions into clean procedural sections with normalized menu references and notes.
- ✅ Completed `03-multi-player-setup.md` by organizing the host/player workflows into clear sections, removing OCR debris, and preserving the truncated `game.def` sample with an explicit note.
- ✅ Completed `04-things-every-stars-player-should-know.md` by removing spillover from the previous chapter and reorganizing the display, saving, launch options, and copy protection material into readable reference sections.
- ✅ Completed `05-the-stars-screen.md` by restructuring the pane walkthrough, command-tile descriptions, scanner modes, and selection summary details into a readable UI reference while cleaning OCR fragments.
- ✅ Completed `06-planets.md` by reorganizing the population, mineral, starbase, mass driver, terraforming, and planet report material into clean sections while removing inline sidebar debris and OCR issues.
- ✅ Completed `07-production.md` by cleaning up queue operations, templates, auto-build behavior, and production constraints into a clearer procedural reference.
- ✅ Completed `08-research.md` by restructuring the research overview, technology browser guidance, allocation rules, and research-cost explanation into cleaner Markdown while removing OCR/layout debris.
- ✅ Completed `09-ship-and-starbase-design.md` by reorganizing ship design, deletion, limits, scanners, cloaking, engines, and enemy-design reference material into readable sections while removing OCR fragments and broken layout spillover.
- ✅ Completed `10-managing-fleets.md` by restructuring fleet movement, finding/switching, fuel use, routing, rendezvous, split/merge, scrapping, and fleet-report guidance into clean Markdown while removing OCR/sidebar debris.
- ✅ Completed `11-navigation.md` by reorganizing waypoint, stargate, and wormhole guidance into clean procedural sections, correcting broken numbering and OCR fragments, and removing stray page-reference debris.
- ✅ Completed `12-colonization.md` by restructuring colonization guidance, planet-selection criteria, freighter workflows, and Alternate Reality notes into clean Markdown while removing OCR/sidebar debris and broken references.
- ✅ Completed `14-transporting-freight.md` by normalizing section headings, numbered procedures, Zip Order guidance, and the mass driver packet workflow while removing OCR/sidebar debris.
- ✅ Completed `15-the-basics-of-combat.md` by reorganizing combat, bombing, packet bombardment, ground combat, and minefield guidance into readable Markdown while replacing broken screenshot/OCR fragments with brief explanatory notes.
- ✅ Completed `16-patrolling.md` by restructuring patrol setup, enemy-relation rules, and battle-plan targeting behavior into clean Markdown while replacing the broken closing cross-reference with a brief note.
- ✅ Completed `17-scanning-and-cloaking.md` by reorganizing scanner types, cloaking rules, detection guidance, tachyon detectors, and stealth piracy into readable Markdown while removing OCR/layout debris and repairing broken examples.
- ✅ Completed `18-reports.md` by reorganizing report usage, keyboard shortcuts, sorting behavior, print-map guidance, and text export details into clean Markdown while removing the broken OCR fragments at the end of the chapter.
- ✅ Completed `19-diplomacy-and-trade.md` by rebuilding the missing split chapter from the PDF source, organizing diplomacy, trade, joint-mining, and orbital-terraforming material into clean Markdown, and omitting the broken sidebar fragment at the end.
- ✅ Completed `20-designing-custom-races.md` by restructuring the custom-race wizard into clean step-based sections, converting the primary and lesser traits into readable Markdown reference lists, and omitting the broken in-game example fragments that did not survive OCR cleanly.
- ✅ Completed `21-predefined-races.md` by removing repeated page-break headings, restructuring each race into consistent subsections, converting strategy text into readable lists where helpful, and correcting obvious OCR and punctuation issues while preserving the original content.
- ✅ Completed `22-alternate-reality-races.md` by recovering the missing chapter text from the appendix spillover, then restructuring population, scanners, factories, mining, defenses, starbases, and colonization into clean Markdown with normalized formulas and terminology.
- ✅ Completed `23-the-guts-of-combat.md` by restructuring the chapter into readable combat-reference sections, normalizing weapon and repair data into lists and tables, and reconstructing the broken movement formula and per-round movement table from the surviving manual text.
- ✅ Completed `24-the-guts-of-cloaking.md` by reconstructing the truncated chapter from the original manual source, restoring the cloaking tables and formulas, and rewriting the OCR-damaged content into clean Markdown reference sections.
- ✅ Completed `25-the-guts-of-mass-drivers.md` by removing the chapter-24 cloaking spillover, restructuring packet decay and damage rules into clean Markdown sections, and omitting the broken closing cross-reference that did not survive OCR cleanly.
- ✅ Completed `26-the-guts-of-minefields.md` by reconstructing the missing chapter from appendix spillover, organizing mine types, detection rules, and race-specific dispenser availability into clean Markdown reference sections.
- ✅ Completed `appendix-a-keyboard-shortcuts.md` by removing the massive chapter spillover, extracting the surviving appendix content, and rewriting it as a clean keyboard-shortcut reference table.
- ✅ Completed `appendix-b-technology-tables.md` by restoring the appendix body from OCR-rendered PDF pages, folding the recovered technology tables back into the chapter, and flagging the pages that still need manual cleanup because of degraded OCR.
- ✅ Completed `appendix-c-files-used-in-stars.md` by reorganizing the appendix into clean file-type reference sections, normalizing filename and `stars.ini` examples, and replacing the trailing OCR spillover with a brief note that the broken fragment continues in Appendix D.
- ✅ Completed `appendix-d-frequently-asked-questions.md` by restructuring the FAQ and glossary into clean Markdown sections, normalizing procedures and terminology, and removing the stray DOS-hosting OCR fragment while preserving the duplicated glossary meaning where it survived in the source.
