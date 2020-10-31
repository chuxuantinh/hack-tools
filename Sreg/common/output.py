#!/usr/bin/env python
# encoding: utf-8
# author: n0tr00t
from string import Template

TEXT_INIT = ("<!DOCTYPE html>\n"
             "<!-- author: n0tr00t -->\n"
             "<html lang=\"en\">\n"
             "  <head>\n"
             "    <meta http-equiv=\"Content-Type\" content=\"text/html; charset=UTF-8\">\n"
             "    <meta charset=\"utf-8\">\n"
             "    <meta http-equiv=\"X-UA-Compatible\" content=\"IE=edge\">\n"
             "    <title>$target - Sreg <Beebeeto></title>\n"
             "    <link href=\"./sreg_tmp/app.css\" rel=\"stylesheet\">\n"
             "    <style>\n"
             "      [ng\\:cloak], [ng-cloak], [data-ng-cloak], [x-ng-cloak], .ng-cloak, .x-ng-cloak {\n"
             "        display: none !important;\n"
             "      }\n"
             "      body {\n"
             "          background-color: #e8e8e8;\n"
             "          color: #000000;\n"
             "      }\n"
             "      header {\n"
             "        background: #151515;\n"
             "        border-top: 0px solid #ffc616;\n"
             "        border-bottom: 3px solid #ffffff;\n"
             "      }\n"
             "      a {\n"
             "        color: #969696;\n"
             "      }\n"
             "    </style>\n"
             "    <script type=\"text/javascript\" src=\"sreg_tmp/jquery.js\"></script>\n"
             "    <script type=\"text/javascript\">\n"
             "    window.onload=function(){\n"
             "        $(\"#detail\").append(\"   Count: \" + $(\".website-name\").length);\n"
             "    }\n"
             "    </script>\n"
             "  </head>\n"
             "  <body class=\"ng-scope\" data-feedly-mini=\"yes\">\n"
             "    <header>\n"
             "      <div class=\"container\">\n"
             "        <div class=\"row\">\n"
             "          <div class=\"logo\">\n"
             "            <a href=\"http://buzz.beebeeto.com/\" target=\"_blank\">\n"
             "              <img src=\"./sreg_tmp/beebeeto_logo.png\" alt=\"beebeeto logo\">\n"
             "            </a>\n"
             "          </div>\n"
             "          <h1 class=\"hidden-xs\" style=\"color: #c62011\">>_ Search Registration</h1>\n"
             "          <h4 style=\"color: #B51D0F\"><p id=\"detail\">$o_type $o_passport  </p></h4>\n"
             "          <h2 class=\"sponsored hidden-xs\" style=\"color: #981C00\">Page Generated by <a href=\"https://buzz.beebeeto.com/\" style=\"color: #c62011\">Sreg</a></h2>\n"
             "        </div>\n"
             "        <div class=\"row\">\n"
             "        </div>\n"
             "      </div>\n"
             "    </header>\n"
             "    <section class=\"\">\n"
             "      <div class=\"container\">\n"
             "        <div class=\"row\">\n"
             "          <div ng-show=\"hasResults\" class=\"col-md-12\">\n"
             "            <table class=\"table table-hover search-results\" id=\"table\">\n"
             "              <thead>\n"
             "                <tr>\n"
             "                  <th class=\"hidden-xs\"><a ng-click=\"sortResults(&#39;Icon&#39;)\">ICON</a></th>\n"
             "                  <th><a ng-click=\"sortResults(&#39;Website&#39;)\">Website</a></th>\n"
             "                  <th class=\"hidden-xs\"><a ng-click=\"sortResults(&#39;Category&#39;)\">Category</a></th>\n"
             "              </tr></thead>\n"
             "              <tbody>\n"
)
TEXT_END = ('              </tbody>\n'
            '            </table>\n'
            '          </div>\n'
            '        </div>\n'
            '      </div>\n'
            '    </section>\n'
            '  </body>\n'
            '</html>\n'
)
TEXT_ADD = ("<tr>\n"
            "    <td class=\"hidden-xs owner\" bind-once=\"result.owner\">\n"
            "        <a href=\"$website_a\" target=\"_blank\"><img src=\"$icon\"></a>\n"
            "    </td>\n"
            "    <td class=\"website-name\">\n"
            "        <h4>\n"
            "          <a bind-attr-once=\"{href: result.website}\" bind-once=\"result.name\" href=\"$website_b\" target=\"_blank\">$app_name</a>\n"
            "        </h4>\n"
            "        <p class=\"description\" bind-attr-once=\"{title: result.description}\" bind-once=\"result.description\" title=\"jQuery Mobile Framework\">\n"
            "            $description\n"
            "        </p>\n"
            "    </td>\n"
            "    <td class=\"hidden-xs owner\" bind-once=\"result.owner\">$category</td>\n"
            "</tr>\n"
)


def output_init(name, output_type, passport):
    file_name = "./reports/" + name + ".html"
    file_object = open(file_name, 'w')
    template_content = Template(TEXT_INIT)
    write_content = template_content.safe_substitute(target=name, o_type=output_type, o_passport=passport)
    file_object.write(write_content)
    file_object.close()


def output_finished(name):
    file_name = "./reports/" + name + ".html"
    file_object = open(file_name, 'a')
    file_object.write(TEXT_END)
    file_object.close()
    print '\n[+] Results the save path: %s' % file_name


def output_add(category, app_name, website, name, passport_type, icon, description):
    file_name = "./reports/" + passport_type + "_" + name + ".html"
    file_object = open(file_name, 'a')
    template_content = Template(TEXT_ADD)
    write_content = template_content.safe_substitute(website_a=website, website_b=website, icon=icon,
                                                     app_name=app_name, description=description, category=category)
    file_object.write(write_content)
    file_object.close()
