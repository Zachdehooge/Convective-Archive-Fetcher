package main

import (
	"github.com/rivo/tview"
)

// TODO: On save, have the city and state get passed in a new page and display it
// TODO: Return the archive in that page // Example found in: https://github.com/Zachdehooge/Weather-Trend-Analyzer/blob/main/outlooks/outlookarchives.py

func main() {
	app := tview.NewApplication()
	form := tview.NewForm().
		AddInputField("City", "", 30, nil, nil).
		AddInputField("State", "", 30, nil, nil).
		AddDropDown("Month", []string{"January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "December"}, 0, nil).
		AddDropDown("Day", []string{"1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31"}, 0, nil).
		AddDropDown("Year", []string{"2000", "2001", "2002", "2003", "2004", "2005", "2006", "2007", "2008", "2009", "2010", "2011", "2012", "2013", "2014", "2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025"}, 0, nil).
		AddTextView("Note: ", "The threshold is optional", 40, 2, true, false).
		AddButton("Save", func() {
			app.Stop()
		}).
		AddButton("Quit", func() {
			app.Stop()
		})
	form.SetBorder(true).SetTitle("Convective Archive").SetTitleAlign(tview.AlignCenter)
	if err := app.SetRoot(form, true).EnableMouse(true).Run(); err != nil {
		panic(err)
	}
}
