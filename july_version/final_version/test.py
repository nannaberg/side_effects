from bs4 import BeautifulSoup
import pandas as pd


table_html = """<table class="pipTable width100Procent glob-padbtm20">
      <tbody><tr class="Header">
        <th class="TableBorder glob-alignCenter" style="padding: 6px; border-bottom: 1px solid #ffffff;" colspan="3">
          <h3>forsigtighed, dosisjustering</h3>
        </th>
      </tr>
      <tr class="Header">
        <th class="TableBorder glob-alignCenter">GFR</th>
        <th class="TableBorder glob-alignCenter">Alder</th>
        <th class="TableBorder glob-alignCenter">Advarsel</th>
      </tr>
      <tr>
        <td class="TableBorder" rowspan="2"><span style="white-space: nowrap;">&lt;30 ml/min.</span></td>
        <td class="TableBorder" rowspan=""><span style="white-space: nowrap;">2-17 år</span></td>
        <td class="TableBorder" rowspan="">
          <p>Højst 15 mg pr. kg legemsvægt 1 gang i døgnet.</p>
        </td>
      </tr>
      <tr>
        <td class="TableBorder" rowspan=""><span style="white-space: nowrap;">≥17 år</span></td>
        <td class="TableBorder" rowspan="">
          <p>Højst 400 mg i.v. 1 gang i døgnet.</p>
        </td>
      </tr>
      <tr>
        <td class="TableBorder" rowspan=""><span style="white-space: nowrap;">30-60 ml/min.</span></td>
        <td class="TableBorder" rowspan=""><span style="white-space: nowrap;">≥17 år</span></td>
        <td class="TableBorder" rowspan="">
          <p>Højst 400 mg i.v. 2 gange i døgnet.</p>
        </td>
      </tr>
    </tbody></table>"""

table_html = """<table class="pipTable width100Procent glob-padbtm20">
      <tbody><tr class="Header">
        <th class="TableBorder glob-alignCenter" style="padding: 6px; border-bottom: 1px solid #ffffff;" colspan="3">
          <h3>forsigtighed, dosisjustering</h3>
        </th>
      </tr>
      <tr class="Header">
        <th class="TableBorder glob-alignCenter">GFR</th>
        <th class="TableBorder glob-alignCenter">Alder</th>
        <th class="TableBorder glob-alignCenter">Advarsel</th>
      </tr>
      <tr>
        <td class="TableBorder" rowspan="2"><span style="white-space: nowrap;">&lt;10 ml/min.</span></td>
        <td class="TableBorder" rowspan=""><span style="white-space: nowrap;">2-12 år</span></td>
        <td class="TableBorder" rowspan="">
          <p>
            </p><div class="floatNone"></div>
            <table width="" class="pipTable contentTable width100Procent">
              <tbody><tr class="Header">
                <th rowspan="" colspan="" width="" style="" class="TableBorder pipTable WhiteBrdBtm TblBrdBtm glob-alignCenter">
	<p><b>Indikation </b>&nbsp;</p>
</th>
                <th rowspan="" colspan="" width="" style="" class="TableBorder TableTHHeaderLast WhiteBrdBtm TblBrdBtm glob-alignCenter">
	<p><b>Højeste dosis </b>&nbsp;</p>
</th>
              </tr>
              <tr class="">
                <td rowspan="" colspan="" width="" style="" class="TableBorder">
	<p>Behandling og forebyggelse af herpes&nbsp;</p>
</td>
                <td rowspan="" colspan="" width="" style="" class="TableBorder">
	<p>125 mg/m<sup>2</sup> legemsoverflade 1 gang dgl.&nbsp;</p>
</td>
              </tr>
              <tr class="">
                <td rowspan="" colspan="" width="" style="" class="TableBorder">
	<p>Herpes zoster og herpes-encefalitis&nbsp;</p>
</td>
                <td rowspan="" colspan="" width="" style="" class="TableBorder">
	<p>250 mg/m<sup>2</sup> legemsoverflade 1 gang dgl.&nbsp;</p>
</td>
              </tr>
              <tr class="">
                <td rowspan="" colspan="2" width="" style="" class="TableBorder">
	<p>Samme dosis ved peritonealdialyse, hæmodialyse <b>og</b> efter hver hæmodialyse.&nbsp;</p>
</td>
              </tr>
            </tbody></table>
            <div class="floatNone padrgt50 SpaceBtm"></div>
          <p></p>
        </td>
      </tr>
      <tr>
        <td class="TableBorder" rowspan=""><span style="white-space: nowrap;">≥12 år</span></td>
        <td class="TableBorder" rowspan="">
          <p>
            </p><div class="floatNone"></div>
            <table width="" class="pipTable contentTable width100Procent">
              <tbody><tr class="Header">
                <th rowspan="" colspan="" width="" style="" class="TableBorder pipTable WhiteBrdBtm TblBrdBtm glob-alignCenter">
	<p><b>Indikation </b>&nbsp;</p>
</th>
                <th rowspan="" colspan="" width="" style="" class="TableBorder TableTHHeaderLast WhiteBrdBtm TblBrdBtm glob-alignCenter">
	<p><b>Højeste dosis </b>&nbsp;</p>
</th>
              </tr>
              <tr class="">
                <td rowspan="" colspan="" width="" style="" class="TableBorder">
	<p>Behandling og forebyggelse af herpes&nbsp;</p>
</td>
                <td rowspan="" colspan="" width="" style="" class="TableBorder">
	<p>2,5 mg/kg legemsvægt 1 gang dgl.&nbsp;</p>
</td>
              </tr>
              <tr class="">
                <td rowspan="" colspan="" width="" style="" class="TableBorder">
	<p>Herpes zoster&nbsp;</p>
</td>
                <td rowspan="" colspan="" width="" style="" class="TableBorder">
	<p>5 mg/kg legemsvægt 1 gang dgl.&nbsp;</p>
</td>
              </tr>
              <tr class="">
                <td rowspan="" colspan="" width="" style="" class="TableBorder">
	<p>Herpes-encefalitis&nbsp;</p>
</td>
                <td rowspan="" colspan="" width="" style="" class="TableBorder">
	<p>7,5 mg/kg legemsvægt 1 gang dgl.&nbsp;</p>
</td>
              </tr>
              <tr class="">
                <td rowspan="" colspan="2" width="" style="" class="TableBorder">
	<p>Samme dosis ved peritonealdialyse, hæmodialyse <b>og</b> efter hver hæmodialyse.&nbsp;</p>
</td>
              </tr>
            </tbody></table>
            <div class="floatNone padrgt50 SpaceBtm"></div>
          <p></p>
        </td>
      </tr>
      <tr>
        <td class="TableBorder" rowspan="2"><span style="white-space: nowrap;">10-25 ml/min.</span></td>
        <td class="TableBorder" rowspan=""><span style="white-space: nowrap;">2-12 år</span></td>
        <td class="TableBorder" rowspan="">
          <p>
            </p><div class="floatNone"></div>
            <table width="" class="pipTable contentTable width100Procent">
              <tbody><tr class="Header">
                <th rowspan="" colspan="" width="" style="" class="TableBorder pipTable WhiteBrdBtm TblBrdBtm glob-alignCenter">
	<p><b>Indikation</b>&nbsp;</p>
</th>
                <th rowspan="" colspan="" width="" style="" class="TableBorder TableTHHeaderLast WhiteBrdBtm TblBrdBtm glob-alignCenter">
	<p><b>Højeste dosis</b>&nbsp;</p>
</th>
              </tr>
              <tr class="">
                <td rowspan="" colspan="" width="" style="" class="TableBorder">
	<p>Behandling og forebyggelse af herpes&nbsp;</p>
</td>
                <td rowspan="" colspan="" width="" style="" class="TableBorder">
	<p>250 mg/m<sup>2</sup> legemsoverflade 1 gang dgl.&nbsp;</p>
</td>
              </tr>
              <tr class="">
                <td rowspan="" colspan="" width="" style="" class="TableBorder">
	<p>Herpes zoster og herpes-encefalitis&nbsp;</p>
</td>
                <td rowspan="" colspan="" width="" style="" class="TableBorder">
	<p>500 mg/m<sup>2</sup> legemsoverflade 1 gang dgl.&nbsp;</p>
</td>
              </tr>
            </tbody></table>
            <div class="floatNone padrgt50 SpaceBtm"></div>
          <p></p>
        </td>
      </tr>
      <tr>
        <td class="TableBorder" rowspan=""><span style="white-space: nowrap;">≥12 år</span></td>
        <td class="TableBorder" rowspan="">
          <p>
            </p><div class="floatNone"></div>
            <table width="" class="pipTable contentTable width100Procent">
              <tbody><tr class="Header">
                <th rowspan="" colspan="" width="" style="" class="TableBorder pipTable WhiteBrdBtm TblBrdBtm glob-alignCenter">
	<p><b>Indikation </b>&nbsp;</p>
</th>
                <th rowspan="" colspan="" width="" style="" class="TableBorder TableTHHeaderLast WhiteBrdBtm TblBrdBtm glob-alignCenter">
	<p><b>Højeste dosis</b>&nbsp;</p>
</th>
              </tr>
              <tr class="">
                <td rowspan="" colspan="" width="" style="" class="TableBorder">
	<p>Behandling og forebyggelse af herpes&nbsp;</p>
</td>
                <td rowspan="" colspan="" width="" style="" class="TableBorder">
	<p>5 mg/kg legemsvægt 1 gang dgl.&nbsp;</p>
</td>
              </tr>
              <tr class="">
                <td rowspan="" colspan="" width="" style="" class="TableBorder">
	<p>Herpes zoster&nbsp;</p>
</td>
                <td rowspan="" colspan="" width="" style="" class="TableBorder">
	<p>10 mg/kg legemsvægt 1 gang dgl.&nbsp;</p>
</td>
              </tr>
              <tr class="">
                <td rowspan="" colspan="" width="" style="" class="TableBorder">
	<p>Herpes-encefalitis&nbsp;</p>
</td>
                <td rowspan="" colspan="" width="" style="" class="TableBorder">
	<p>15 mg/kg legemsvægt 1 gang dgl.&nbsp;</p>
</td>
              </tr>
            </tbody></table>
            <div class="floatNone padrgt50 SpaceBtm"></div>
          <p></p>
        </td>
      </tr>
      <tr>
        <td class="TableBorder" rowspan="2"><span style="white-space: nowrap;">25-50 ml/min.</span></td>
        <td class="TableBorder" rowspan=""><span style="white-space: nowrap;">2-12 år</span></td>
        <td class="TableBorder" rowspan="">
          <p>
            </p><div class="floatNone"></div>
            <table width="" class="pipTable contentTable width100Procent">
              <tbody><tr class="Header">
                <th rowspan="" colspan="" width="" style="" class="TableBorder pipTable WhiteBrdBtm TblBrdBtm glob-alignCenter">
	<p><b>Indikation </b>&nbsp;</p>
</th>
                <th rowspan="" colspan="" width="" style="" class="TableBorder TableTHHeaderLast WhiteBrdBtm TblBrdBtm glob-alignCenter">
	<p><b>Højeste dosis </b>&nbsp;</p>
</th>
              </tr>
              <tr class="">
                <td rowspan="" colspan="" width="" style="" class="TableBorder">
	<p>Behandling og forebyggelse af herpes&nbsp;</p>
</td>
                <td rowspan="" colspan="" width="" style="" class="TableBorder">
	<p>250 mg/m<sup>2</sup> legemsoverflade hver 12. time&nbsp;</p>
</td>
              </tr>
              <tr class="">
                <td rowspan="" colspan="" width="" style="" class="TableBorder">
	<p>Herpes zoster og herpes-encefalitis&nbsp;</p>
</td>
                <td rowspan="" colspan="" width="" style="" class="TableBorder">
	<p>500 mg/m<sup>2</sup> legemsoverflade hver 12. time&nbsp;</p>
</td>
              </tr>
            </tbody></table>
            <div class="floatNone padrgt50 SpaceBtm"></div>
          <p></p>
        </td>
      </tr>
      <tr>
        <td class="TableBorder" rowspan=""><span style="white-space: nowrap;">≥12 år</span></td>
        <td class="TableBorder" rowspan="">
          <p>
            </p><div class="floatNone"></div>
            <table width="" class="pipTable contentTable width100Procent">
              <tbody><tr class="Header">
                <th rowspan="" colspan="" width="" style="" class="TableBorder pipTable WhiteBrdBtm TblBrdBtm glob-alignCenter">
	<p><b>Indikation </b>&nbsp;</p>
</th>
                <th rowspan="" colspan="" width="" style="" class="TableBorder TableTHHeaderLast WhiteBrdBtm TblBrdBtm glob-alignCenter">
	<p><b>Højeste dosis </b>&nbsp;</p>
</th>
              </tr>
              <tr class="">
                <td rowspan="" colspan="" width="" style="" class="TableBorder">
	<p>Behandling og forebyggelse af herpes&nbsp;</p>
</td>
                <td rowspan="" colspan="" width="" style="" class="TableBorder">
	<p>5 mg/kg legemsvægt hver 12. time&nbsp;</p>
</td>
              </tr>
              <tr class="">
                <td rowspan="" colspan="" width="" style="" class="TableBorder">
	<p>Herpes zoster&nbsp;</p>
</td>
                <td rowspan="" colspan="" width="" style="" class="TableBorder">
	<p>10 mg/kg legemsvægt hver 12. time&nbsp;</p>
</td>
              </tr>
              <tr class="">
                <td rowspan="" colspan="" width="" style="" class="TableBorder">
	<p>Herpes-encefalitis&nbsp;</p>
</td>
                <td rowspan="" colspan="" width="" style="" class="TableBorder">
	<p>15 mg/kg legemsvægt hver 12. time&nbsp;</p>
</td>
              </tr>
            </tbody></table>
            <div class="floatNone padrgt50 SpaceBtm"></div>
          <p></p>
        </td>
      </tr>
    </tbody></table>"""

soup = BeautifulSoup(table_html, "lxml")
df = pd.read_html(str(soup), flavor="lxml")
print(df[0])
df[0].to_excel("output.xlsx")


# importpypandoc

# html_content = """<ol class="cstlDefaultStyle cstl0" style="position: relative; padding-top:0pt;text-align:left;padding-left:63pt;text-indent:0pt;list-style-type:none;">
#    <li><span style="font-size:12pt;">●&nbsp;Overfølsomhed over for losartan, sulfonamid-afledte stoffer (som hydrochlorthiazid) eller over for et eller flere af hjælpestofferne anført i pkt. 6.1.</span></li>
#   </ol>"""

# markdown = pypandoc.convert_text(html_content, 'markdown', format='html')

# print(markdown)

# import pandas as pd

# # Sample data for the first table
# data1 = {
#     "GFR": ["<10 ml/min."],
#     "Advarsel": [
#         "En stigning i AUC på 33% for azithromycin er set ved GFR < 10 ml/min. Forsigtighed tilrådes."
#     ],
# }

# # Sample data for the second table
# data2 = {
#     "GFR": ["<10 ml/min.", "≥12 år"],
#     "Alder": ["2-12 år", "≥12 år"],
#     "Indikation": [
#         "Behandling og forebyggelse af herpes",
#         "Behandling og forebyggelse af herpes",
#     ],
#     "Højeste dosis": [
#         "125 mg/m² legemsoverflade 1 gang dgl.",
#         "5 mg/kg legemsvægt 1 gang dgl.",
#     ],
# }

# # Create DataFrames
# df1 = pd.DataFrame(data1)
# df2 = pd.DataFrame(data2)

# # Write to Excel with both tables in the same sheet
# with pd.ExcelWriter("tables_combined.xlsx") as writer:
#     # Write the first table
#     df1.to_excel(writer, sheet_name="Combined Tables", startrow=0, index=False)

#     # Write the second table with an offset
#     df2.to_excel(
#         writer, sheet_name="Combined Tables", startrow=len(df1) + 4, index=False
#     )  # 4 rows gap

#     # Add headings (if desired, customize as needed)
#     workbook = writer.book
#     worksheet = writer.sheets["Combined Tables"]

#     # Merge cells for headings
#     worksheet.merge_cells("A1:B1")
#     worksheet["A1"] = "Forsigtighed, Øget Bivirkningsrisiko"
#     # worksheet["A1"].font = workbook.create_font(bold=True)

#     worksheet.merge_cells(f"A{len(df1) + 5}:D{len(df1) + 5}")
#     worksheet[f"A{len(df1) + 5}"] = "Forsigtighed, Dosisjustering"
#     # worksheet[f"A{len(df1) + 5}"].font = workbook.create_font(bold=True)

#     # Save the file
#     writer.save()
