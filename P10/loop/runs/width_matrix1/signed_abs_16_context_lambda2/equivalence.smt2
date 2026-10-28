; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(assert
 (let ((?x44 ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) c)))))))))
(let ((?x6 ((_ extract 15 0) ((_ extract 15 0) (bvadd ((_ extract 15 0) ((_ extract 15 0) b)) ((_ extract 15 0) ((_ extract 15 0) a)))))))
(let (($x159 (and (distinct (ite (bvsge a (_ bv0 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x19 (ite $x159 (bvadd ((_ extract 15 0) (ite (bvslt a (_ bv0 16)) (bvneg a) a)) ((_ extract 15 0) b)) c)))
(and (distinct ?x19 (ite $x159 ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ?x6)))) ?x44)) true))))))
(check-sat)
