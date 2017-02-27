#coding=utf8
class Rule(object):
    def action(self,block,handler):
        handler.start(self.type)
        handler.feed(block)
        handler.end(self.type)
        return True
class HeadingRule(Rule):
    '''标题是一个最多70个字符的行，不以冒号结束'''
    type = 'heading'
    def condition(self,block):
        return not '\n' in block and len(block)<=50 and not block[:-1] == ':'
class TitleRule(HeadingRule):
    '''题目是文档的第一个块，作为标题存在'''
    type = 'title'
    first = True

    def condition(self,block):
        if not self.first:return False
        self.first = False
        return HeadingRule.condition(self,block)
class ListItemRule(Rule):
    '''列表项是以连字符作为开始的段落，作为格式化的一部分，连字符会被删除'''
    type = 'listitem'
    def condition(self,block):
        return block[0] == '-'
    def action(self,block,handler):
        handler.start(self.type)
        handler.feed(block[1:].strip())
        handler.end(self.type)
        return True
class ListRule(ListItemRule):
    '''列表开始于并非列表项的块和随后的列表项之间，由最后一个连续的列表项作为结束'''
    type = 'list'
    inside = False
    def condition(self,block):
        return True
    def action(self,block,handler):
        if not self.inside and ListItemRule.condition(self,block):
            handler.start(self.type)
            self.inside = True            
        elif self.inside and not ListItemRule.condition(self,block):
            handler.end(self.type)
            self.inside = False
        return False
class ParagraphRule(Rule):
    '''段落是不符合其他规则的块'''
    type = 'paragraph'
    def condition(self,block):
        return True